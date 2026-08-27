#!/usr/bin/env python3
"""
ai_enhancer.py — MercatoPULSE V2 Groq Brain Engine

Architecture : UN SEUL appel Groq par article qui fait TOUT :
  1. Extraction d'entités (joueur, clubs, montant, ligue)
  2. Classification de statut (OFFICIEL / HERE WE GO / NEGOCIATION / RUMEUR)
  3. Scoring de crédibilité dynamique (1-5)
  4. Hash sémantique pour déduplication
  5. Rédaction titre + résumé style Fabrizio Romano

Fallback garanti : si Groq échoue → moteur NLP local (coût 0€)
Rate Limiting : backoff exponentiel + batch de 5 articles max
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# RATE LIMITER — Respect des quotas Groq (30 req/min gratuit)
# ─────────────────────────────────────────────────────────────
_last_call_ts: float = 0.0
_MIN_INTERVAL: float = 2.2  # ~27 req/min, marge de sécurité

def _rate_limit():
    """Attend si nécessaire pour respecter le rate limit Groq."""
    global _last_call_ts
    now = time.time()
    elapsed = now - _last_call_ts
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_call_ts = time.time()


# ─────────────────────────────────────────────────────────────
# SYSTEM PROMPT — Le cerveau Groq
# ─────────────────────────────────────────────────────────────
GROQ_SYSTEM_PROMPT = """Tu es un expert journaliste football spécialisé dans les transferts, inspiré par Fabrizio Romano.

Tu reçois un article brut de news football (possiblement en français, anglais, espagnol, italien, allemand ou arabe).
Tu dois analyser cet article et retourner un JSON structuré avec les champs suivants :

{
  "player_name": "Nom complet du joueur principal (ex: Ferran Torres). Vide si aucun joueur identifié.",
  "from_club": "Le club VENDEUR = le club ACTUEL du joueur, celui qu'il QUITTE. Vide si non identifié.",
  "to_club": "Le club ACHETEUR = la DESTINATION du joueur, celui qui le RECRUTE. Vide si non identifié.",
  "transfer_fee": "Montant du transfert en texte (ex: '45 M€', 'Prêt avec option d'achat', 'Libre'). 'Non communiqué' si inconnu.",
  "fee_numeric": 0,
  "league": "Le championnat principal concerné parmi : Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿, La Liga 🇪🇸, Ligue 1 🇫🇷, Serie A 🇮🇹, Bundesliga 🇩🇪, Saudi Pro League 🇸🇦, Champions League 🇪🇺",
  "status": "Un parmi : OFFICIEL ✅, HERE WE GO 🔥, NEGOCIATION 💬, RUMEUR 📰",
  "credibility": 4.5,
  "national_team": "Sélection nationale du joueur si connue (ex: France 🇫🇷). Vide sinon.",
  "semantic_hash": "identifiant unique normalisé du transfert (ex: ferran_torres__fc_barcelone__psg)",
  "fabrizio_title": "Titre accrocheur en FRANÇAIS au style Fabrizio Romano, commençant par le statut emoji",
  "fabrizio_summary": "Résumé structuré en FRANÇAIS avec des bullet points emoji (🚨, 🤝, 💶, 🩺, 📝, 💬)"
}

RÈGLES CRITIQUES — DIRECTION DU TRANSFERT (NE PAS INVERSER !) :
1. from_club = le club ACTUEL du joueur, d'où il PART. C'est le VENDEUR.
   Exemples : "Kevin De Bruyne quitte Manchester City" → from_club = "Manchester City"
              "Le PSG vend Neymar" → from_club = "PSG"
              "Hakimi prolonge au PSG" → from_club = "PSG", to_club = "PSG" (prolongation)
2. to_club = le club de DESTINATION, celui qui ACHÈTE/RECRUTE le joueur.
   Exemples : "Kevin De Bruyne signe au Bayern Munich" → to_club = "Bayern Munich"
              "Le Real Madrid recrute Florian Wirtz" → to_club = "Real Madrid"
3. Si l'article dit "X rejoint Y" ou "X signe à Y" → from_club = club actuel de X, to_club = Y.
4. Si l'article dit "Y recrute X" ou "Y s'offre X" → to_club = Y, from_club = club actuel de X.
5. Pour une PROLONGATION : from_club = to_club = le même club.
6. fee_numeric = montant en millions d'euros (nombre). 0 si inconnu, prêt ou libre.
7. credibility = note de 1 à 5 basée sur la certitude du langage source (ex: "confirmed" = 5, "rumoured" = 2).
8. semantic_hash = joueur__club_from__club_to en minuscules, underscores, sans accents. Ce hash permet de regrouper les doublons.
9. fabrizio_title DOIT commencer par le statut : "🚨 OFFICIEL :" ou "🔥 HERE WE GO :" ou "💬 NÉGOCIATION :" ou "📰 RUMEUR :"
10. fabrizio_summary DOIT contenir 3-5 bullet points avec emojis, terminant par "💬 Note ce transfert de 1 à 10 ! ⏬"
11. TOUJOURS répondre en JSON valide, sans texte autour.
12. Si l'article N'EST PAS un transfert football, retourne {"is_football": false}.
"""


def _build_user_prompt(title: str, summary: str, source: str, lang: str) -> str:
    """Construit le prompt utilisateur pour Groq."""
    return f"""Analyse cet article de transfert football :

Source : {source}
Langue : {lang}
Titre : {title}
Résumé : {summary}"""


# ─────────────────────────────────────────────────────────────
# GROQ API CALL — Avec retry et backoff exponentiel
# ─────────────────────────────────────────────────────────────
def _call_groq_api(title: str, summary: str, source: str = "", lang: str = "fr", max_retries: int = 2) -> Optional[Dict]:
    """
    Appelle l'API Groq avec le system prompt expert.
    Retourne le JSON parsé ou None en cas d'échec.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    try:
        import requests
    except ImportError:
        return None

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": GROQ_SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(title, summary, source, lang)},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.15,
        "max_tokens": 800,
    }

    for attempt in range(max_retries + 1):
        try:
            _rate_limit()
            r = requests.post(url, headers=headers, json=payload, timeout=8)

            if r.status_code == 429:
                # Rate limited — attendre et réessayer
                wait = (2 ** attempt) * 3
                logger.warning("Groq rate limited, waiting %ds...", wait)
                time.sleep(wait)
                continue

            if r.ok:
                data = r.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)

                # Vérifier si l'article est football
                if parsed.get("is_football") is False:
                    return {"is_football": False}

                return parsed

            logger.warning("Groq API error %d: %s", r.status_code, r.text[:200])

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning("Groq response parse error: %s", e)
        except Exception as e:
            logger.warning("Groq API call failed (attempt %d): %s", attempt, e)

        if attempt < max_retries:
            time.sleep(1.5 * (attempt + 1))

    return None


# ─────────────────────────────────────────────────────────────
# FALLBACK LOCAL — Moteur NLP local (coût 0€)
# ─────────────────────────────────────────────────────────────
def _local_fallback(title: str, summary: str, source: str = "") -> Dict[str, Any]:
    """
    Analyse locale via le moteur NLP existant.
    Utilisé quand Groq n'est pas disponible ou échoue.
    """
    from src.mercato_nlp import parse_article_full
    from src.ai_organizer import classify_article, analyze_sentiment

    entities = parse_article_full(title, summary)
    player = entities.get("player_name", "")
    from_c = entities.get("from_club", "")
    to_c = entities.get("to_club", "")
    status = entities.get("status", "RUMEUR 📰")
    fee = entities.get("transfer_fee", "Non communiqué")
    nat = entities.get("national_team", "")

    # Fee numeric extraction
    fee_num = 0.0
    if fee and fee != "Non communiqué":
        m = re.search(r"(\d+[\.,]?\d*)", fee)
        if m:
            fee_num = float(m.group(1).replace(",", "."))

    # Classification
    cat = classify_article({"title": title, "summary": summary, "source": source})

    # Semantic hash
    sem = _make_semantic_hash(player, from_c, to_c)

    # Fabrizio Romano formatting
    if "OFFICIEL" in status:
        header = "🚨 OFFICIEL :"
    elif "HERE WE GO" in status:
        header = "🔥 HERE WE GO :"
    elif "NEGOCIATION" in status:
        header = "💬 NÉGOCIATION :"
    else:
        header = "📰 RUMEUR :"

    if player and to_c and from_c and from_c != to_c:
        fab_title = f"{header} {player} quitte {from_c} pour {to_c} — {fee}"
    elif player and to_c:
        fab_title = f"{header} {player} en route vers {to_c}"
    elif player:
        fab_title = f"{header} Mise à jour sur l'avenir de {player}"
    else:
        fab_title = f"{header} {title}"

    bullets = []
    if player and to_c:
        bullets.append(f"🚨 {to_c} a trouvé un accord pour {player}.")
    elif player:
        bullets.append(f"🚨 Mise à jour importante sur l'avenir de {player}.")
    else:
        bullets.append(f"🚨 {title}")

    if from_c and to_c and from_c != to_c:
        bullets.append(f"🤝 Négociations avancées entre {from_c} et {to_c}.")
    elif from_c == to_c and from_c:
        bullets.append(f"📝 Prolongation de contrat avec {from_c}.")

    if fee and fee != "Non communiqué":
        bullets.append(f"💶 Montant convenu : {fee} + bonus et variables.")

    bullets.append("🩺 Visite médicale prévue, termes personnels acceptés.")
    bullets.append("💬 Note ce transfert de 1 à 10 ! ⏬")

    return {
        "player_name": player,
        "from_club": from_c,
        "to_club": to_c,
        "transfer_fee": fee,
        "fee_numeric": fee_num,
        "league": cat,
        "status": status,
        "credibility": 4.0,
        "semantic_hash": sem,
        "fabrizio_title": fab_title,
        "fabrizio_summary": "\n\n".join(bullets),
        "national_team": nat,
    }


# ─────────────────────────────────────────────────────────────
# SEMANTIC HASH — Pour déduplication
# ─────────────────────────────────────────────────────────────
def _normalize_for_hash(s: str) -> str:
    """Normalise une chaîne pour le hash sémantique."""
    import unicodedata
    s = unicodedata.normalize("NFD", s.lower().strip())
    s = re.sub(r"[\u0300-\u036f]", "", s)
    s = re.sub(r"[^a-z0-9]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def _make_semantic_hash(player: str, from_club: str, to_club: str) -> str:
    """Génère un hash sémantique unique pour un transfert."""
    p = _normalize_for_hash(player or "unknown")
    f = _normalize_for_hash(from_club or "unknown")
    t = _normalize_for_hash(to_club or "unknown")
    return f"{p}__{f}__{t}"


def _validate_club_direction(result: Dict[str, Any], title: str = "", summary: str = "") -> Dict[str, Any]:
    """
    Valide et garantit la direction exacte d'un transfert (club vendeur -> club acheteur)
    en s'appuyant sur le moteur d'analyse grammaticale multilingue.
    """
    player_name = result.get("player_name", "")
    from_club = result.get("from_club", "")
    to_club = result.get("to_club", "")

    text_to_check = f"{title} {summary} {result.get('fabrizio_title', '')} {result.get('fabrizio_summary', '')}".strip()
    if text_to_check:
        try:
            from src.mercato_nlp import resolve_mercato_direction, PLAYER_REGISTRY
            p_data = PLAYER_REGISTRY.get(player_name)
            correct_from, correct_to = resolve_mercato_direction(text_to_check, "", player_name, p_data)
            if correct_from and correct_to and correct_from != correct_to:
                result["from_club"] = correct_from
                result["to_club"] = correct_to
            elif correct_to and not to_club:
                result["to_club"] = correct_to
            elif correct_from and not from_club:
                result["from_club"] = correct_from
        except Exception as e:
            logger.warning("Club direction validation error: %s", e)

    return result

# ─────────────────────────────────────────────────────────────
# POINT D'ENTRÉE PRINCIPAL — groq_analyze_article()
# ─────────────────────────────────────────────────────────────
def groq_analyze_article(
    title: str,
    summary: str,
    source: str = "",
    lang: str = "fr",
    current_image: str = "",
) -> Dict[str, Any]:
    """
    Point d'entrée principal du Groq Brain Engine.
    
    Un SEUL appel qui fait TOUT :
      - Extraction d'entités
      - Classification ligue + statut
      - Scoring de crédibilité
      - Rédaction Fabrizio Romano
      - Hash sémantique pour déduplication
    
    Fallback automatique sur le moteur local si Groq échoue.
    """
    # 1. Essayer Groq API
    groq_result = _call_groq_api(title, summary, source, lang)

    if groq_result:
        # Article non-football détecté par Groq
        if groq_result.get("is_football") is False:
            return {"is_football": False}

        # Compléter les champs manquants avec des défauts
        result = {
            "player_name": groq_result.get("player_name", "") or "",
            "from_club": groq_result.get("from_club", "") or "",
            "to_club": groq_result.get("to_club", "") or "",
            "transfer_fee": groq_result.get("transfer_fee", "Non communiqué") or "Non communiqué",
            "fee_numeric": float(groq_result.get("fee_numeric", 0) or 0),
            "league": groq_result.get("league", "Champions League 🇪🇺") or "Champions League 🇪🇺",
            "status": groq_result.get("status", "RUMEUR 📰") or "RUMEUR 📰",
            "credibility": float(groq_result.get("credibility", 4.0) or 4.0),
            "semantic_hash": groq_result.get("semantic_hash", "") or "",
            "fabrizio_title": groq_result.get("fabrizio_title", title) or title,
            "fabrizio_summary": groq_result.get("fabrizio_summary", summary) or summary,
            "national_team": groq_result.get("national_team", "") or "",
            "_source": "groq",
        }

        # ── POST-VALIDATION : Corriger l'inversion from_club ↔ to_club ──
        # Utiliser la base PLAYER_REGISTRY pour vérifier que from_club = club actuel du joueur
        result = _validate_club_direction(result)

        # Recalculer le hash sémantique si absent
        if not result["semantic_hash"]:
            result["semantic_hash"] = _make_semantic_hash(
                result["player_name"], result["from_club"], result["to_club"]
            )

        logger.info("✅ Groq Brain: %s → %s | %s → %s",
                     result["player_name"] or "?",
                     result["to_club"] or "?",
                     result["status"],
                     result["semantic_hash"][:30])
        return result

    # 2. Fallback sur le moteur local
    logger.info("⚡ Fallback local pour: %s", title[:60])
    result = _local_fallback(title, summary, source)
    result["_source"] = "local"
    return result


# ─────────────────────────────────────────────────────────────
# BATCH PROCESSING — Traitement par lots
# ─────────────────────────────────────────────────────────────
def groq_analyze_batch(
    articles: List[Dict[str, str]],
    batch_size: int = 5,
) -> List[Dict[str, Any]]:
    """
    Traite un lot d'articles via le Groq Brain Engine.
    Respecte le rate limiting avec des pauses entre les batches.
    """
    results = []
    total = len(articles)

    for i, art in enumerate(articles):
        title = str(art.get("title", ""))
        summary = str(art.get("summary", ""))
        source = str(art.get("source", ""))
        lang = str(art.get("language", "fr"))
        img = str(art.get("image_url", ""))

        result = groq_analyze_article(title, summary, source, lang, img)
        results.append(result)

        if (i + 1) % 10 == 0:
            logger.info("📊 Groq Brain progress: %d/%d articles", i + 1, total)

    return results
