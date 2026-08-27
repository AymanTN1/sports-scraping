"""
ai_organizer.py — MercatoPulse Football Transfer & Mercato NLP Engine
1. Classification des articles par Championnat/Ligue (Premier League, La Liga, Ligue 1, Serie A, Bundesliga, Saudi Pro League, etc.)
2. Extraction d'entités Mercato précises (Joueurs, Club Vendeur, Club Acheteur, Montant du Transfert, Statut du Transfert, Sélection Nationale)
3. Analyse de Statut : OFFICIEL ✅, HERE WE GO 🔥, NEGOCIATION 💬, RUMEUR 📰
"""

from __future__ import annotations

import os
import sys
import re
import unicodedata
from urllib.parse import unquote
import pandas as pd

# Standardize sys.path for root imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─────────────────────────────────────────────
# LIGUES & CHAMPIONNATS FOOTBALL
# ─────────────────────────────────────────────
LEAGUE_KEYWORDS: dict[str, list[str]] = {
    "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿": [
        "premier league", "manchester city", "man city", "arsenal", "liverpool", "manchester united", "man utd",
        "chelsea", "tottenham", "spurs", "newcastle", "aston villa", "west ham", "brighton", "everton", "brentford",
        "crystal palace", "wolverhampton", "wolves", "fulham", "bournemouth", "nottingham forest", "england", "angletterre"
    ],
    "La Liga 🇪🇸": [
        "la liga", "la liga santander", "real madrid", "barcelona", "barça", "fc barcelone", "atletico madrid",
        "atlético", "sevilla", "séville", "real betis", "villareal", "villarreal", "athletic bilbao", "real sociedad", "girona", "espagne", "spain"
    ],
    "Ligue 1 🇫🇷": [
        "ligue 1", "psg", "paris saint-germain", "olympique de marseille", "om", "olympique lyonnais", "ol", "lyon",
        "monaco", "as monaco", "lille", "losc", "rennes", "stade rennais", "nice", "ogc nice", "lens", "rc lens",
        "strasbourg", "nantes", "toulouse", "france", "ligue1"
    ],
    "Serie A 🇮🇹": [
        "serie a", "inter milan", "inter", "ac milan", "juventus", "juve", "napoli", "naples", "roma", "as roma",
        "lazio", "atala", "atalanta", "fiorentina", "bologna", "italie", "italy"
    ],
    "Bundesliga 🇩🇪": [
        "bundesliga", "bayern munich", "bayern", "borussia dortmund", "dortmund", "bvb", "bayer leverkusen",
        "leverkusen", "rb leipzig", "leipzig", "eintracht frankfurt", "stuttgart", "allemagne", "germany"
    ],
    "Saudi Pro League 🇸🇦": [
        "saudi pro league", "al nassr", "al-nassr", "al hilal", "al-hilal", "al ittihad", "al-ittihad",
        "al ahli", "al-ahli", "saudi", "arabie saoudite", "saudi league"
    ],
    "Champions League 🇪🇺": [
        "champions league", "ligue des champions", "c1", "uefa", "europa league", "conference league"
    ],
}

# ─────────────────────────────────────────────
# JOUEURS & SÉLECTIONS NATIONALES
# ─────────────────────────────────────────────
PLAYER_NATIONALITY: dict[str, str] = {
    "Kylian Mbappé": "France 🇫🇷",
    "Erling Haaland": "Norvège 🇳🇴",
    "Lamine Yamal": "Espagne 🇪🇸",
    "Jude Bellingham": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Vinicius Jr": "Brésil 🇧🇷",
    "Victor Osimhen": "Nigéria 🇳🇬",
    "Florian Wirtz": "Allemagne 🇩🇪",
    "Mohamed Salah": "Égypte 🇪🇬",
    "Achraf Hakimi": "Maroc 🇲🇦",
    "Ousmane Dembélé": "France 🇫🇷",
    "Kevin De Bruyne": "Belgique 🇧🇪",
    "Luka Modric": "Croatie 🇭🇷",
    "Antoine Griezmann": "France 🇫🇷",
    "Neymar": "Brésil 🇧🇷",
    "Cristiano Ronaldo": "Portugal 🇵🇹",
    "Lionel Messi": "Argentine 🇦🇷",
    "Marcus Rashford": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Alexander Isak": "Suède 🇸🇪",
    "Bruno Fernandes": "Portugal 🇵🇹",
    "Gianluigi Donnarumma": "Italie 🇮🇹",
    "Lautaro Martinez": "Argentine 🇦🇷",
    "Harry Kane": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Bukayo Saka": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Phil Foden": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Declan Rice": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Cole Palmer": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Pedri": "Espagne 🇪🇸",
    "Gavi": "Espagne 🇪🇸",
    "Rodri": "Espagne 🇪🇸",
    "Nico Williams": "Espagne 🇪🇸",
    "Dani Olmo": "Espagne 🇪🇸",
    "Endrick": "Brésil 🇧🇷",
    "Estevao": "Brésil 🇧🇷",
    "Viktor Gyökeres": "Suède 🇸🇪",
    "Federico Valverde": "Uruguay 🇺🇾",
    "Eduardo Camavinga": "France 🇫🇷",
    "Aurélien Tchouaméni": "France 🇫🇷",
    "William Saliba": "France 🇫🇷",
    "Theo Hernandez": "France 🇫🇷",
    "Michael Olise": "France 🇫🇷",
    "Bradley Barcola": "France 🇫🇷",
    "Warren Zaïre-Emery": "France 🇫🇷",
    "Rodrygo": "Brésil 🇧🇷",
    "Julian Alvarez": "Argentine 🇦🇷",
    "Alexis Mac Allister": "Argentine 🇦🇷",
    "Enzo Fernandez": "Argentine 🇦🇷",
    "Trent Alexander-Arnold": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Virgil van Dijk": "Pays-Bas 🇳🇱",
    "Xavi Simons": "Pays-Bas 🇳🇱",
    "Cody Gakpo": "Pays-Bas 🇳🇱",
    "Frenkie de Jong": "Pays-Bas 🇳🇱",
    "Jamal Musiala": "Allemagne 🇩🇪",
    "Leroy Sané": "Allemagne 🇩🇪",
    "Kai Havertz": "Allemagne 🇩🇪",
    "Joshua Kimmich": "Allemagne 🇩🇪",
    "Rafael Leao": "Portugal 🇵🇹",
    "Bernardo Silva": "Portugal 🇵🇹",
    "Rúben Dias": "Portugal 🇵🇹",
    "Joao Neves": "Portugal 🇵🇹",
    "Leny Yoro": "France 🇫🇷",
    "Khvicha Kvaratskhelia": "Géorgie 🇬🇪",
    "Nicolo Barella": "Italie 🇮🇹",
    "Alessandro Bastoni": "Italie 🇮🇹",
    "Federico Chiesa": "Italie 🇮🇹",
    "Brahim Diaz": "Maroc 🇲🇦",
    "Nayef Aguerd": "Maroc 🇲🇦",
    "Azzedine Ounahi": "Maroc 🇲🇦",
    "Alphonso Davies": "Canada 🇨🇦",
    "Khvicha Kvaratskhelia": "Géorgie 🇬🇪",
}

KNOWN_PLAYERS = list(PLAYER_NATIONALITY.keys())

KNOWN_CLUBS = [
    "Real Madrid", "FC Barcelone", "PSG", "Manchester City", "Arsenal", "Liverpool", "Manchester United",
    "Chelsea", "Bayern Munich", "Juventus", "Inter Milan", "AC Milan", "Atlético de Madrid", "Bayer Leverkusen",
    "Borussia Dortmund", "Al-Nassr", "Al-Hilal", "Al-Ittihad", "AS Monaco", "Olympique de Marseille", "Olympique Lyonnais",
    "Aston Villa", "Newcastle", "Tottenham", "Sporting CP", "Benfica", "FC Porto", "Napoli", "Roma", "West Ham", "Girona"
]

# ─────────────────────────────────────────────
# REGEX DETECTION DE MONTANTS
# ─────────────────────────────────────────────
FEE_PATTERNS = [
    r"(\d+[\.,]?\d*\s*(?:M€|millions?|M\$|M£|millions d'euros|million))",
    r"(gratuit|fin de contrat|free transfer|libre|prêt|loan)",
    r"(clause de \d+[\.,]?\d*\s*M€)",
]


def normalize_text(text: str) -> str:
    """Normalise le texte pour le matching NLP."""
    if not text:
        return ""
    text = unquote(str(text))
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_numeric_fee(fee_str: str) -> float:
    """Extrait le montant numérique en Millions d'€ depuis une chaîne."""
    if not fee_str:
        return 0.0
    s = fee_str.lower()
    if "gratuit" in s or "free" in s or "prêt" in s or "loan" in s or "libre" in s:
        return 0.0
    match = re.search(r"(\d+[\.,]?\d*)", s)
    if match:
        try:
            val = float(match.group(1).replace(",", "."))
            return val
        except ValueError:
            return 0.0
    return 0.0


def analyze_sentiment(title: str, summary: str) -> str:
    """Détermine la tendance/Hype de l'information Mercato."""
    text = f"{title} {summary}".lower()
    if any(k in text for k in ["accord", "hot", "brûlant", "signe", "proche", "top", "avance", "record", "here we go"]):
        return "Bullish"
    elif any(k in text for k in ["capote", "refus", "bloqué", "rejeté", "blessure", "échec", "froid", "avorté"]):
        return "Bearish"
    return "Neutre"


def classify_article(article: dict | str) -> str:
    """Classifie un article selon son championnat/ligue."""
    if isinstance(article, str):
        text = article
    else:
        text = f"{article.get('title', '')} {article.get('summary', '')} {article.get('category', '')}"
    
    norm = normalize_text(text)
    for league, kws in LEAGUE_KEYWORDS.items():
        for kw in kws:
            if kw in norm:
                return league
    return "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿"


def extract_mercato_entities(title: str, summary: str = "") -> dict:
    """
    Extrait avec haute précision les entités du transfert via le moteur mercato_nlp.
    """
    from src.mercato_nlp import parse_article_full
    return parse_article_full(title, summary)


def process_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    MercatoPULSE V2 — Pipeline d'analyse via Groq Brain Engine.
    
    Un SEUL appel Groq par article qui fait TOUT :
      - Extraction d'entités (joueur, clubs, montant)
      - Classification (ligue, statut)
      - Scoring de crédibilité
      - Rédaction Fabrizio Romano
      - Hash sémantique pour déduplication
    
    Fallback garanti sur le moteur NLP local si Groq échoue.
    """
    if df.empty:
        return df

    from src.photo_enricher import resolve_photo_for_article
    from src.ai_enhancer import groq_analyze_article
    from src.deduplicator import deduplicate_dataframe

    def _process_one_row(row_tuple):
        _, row = row_tuple
        title = str(row.get("title", ""))
        summary = str(row.get("summary", ""))
        source = str(row.get("source", ""))
        lang = str(row.get("language", "fr"))
        url = str(row.get("url", ""))
        curr_img = str(row.get("image_url") or "")

        result = groq_analyze_article(
            title=title,
            summary=summary,
            source=source,
            lang=lang,
            current_image=curr_img,
        )

        if result.get("is_football") is False:
            return None

        p_name = result.get("player_name", "")
        f_club = result.get("from_club", "")
        t_club = result.get("to_club", "")
        st = result.get("status", "RUMEUR 📰")
        fee_str = result.get("transfer_fee", "Non communiqué")
        fee_n = float(result.get("fee_numeric", 0) or 0)
        cat = result.get("league", "Champions League 🇪🇺")
        nat = result.get("national_team", "")
        sem = result.get("semantic_hash", "")
        cred = float(result.get("credibility", 4.0) or 4.0)

        if "OFFICIEL" in st or "HERE WE GO" in st:
            sent = "Positif"
        elif "NEGOCIATION" in st:
            sent = "Neutre"
        else:
            sent = "Neutre"

        best_img = resolve_photo_for_article(
            article_url=url,
            player_name=p_name,
            to_club=t_club,
            from_club=f_club,
            current_image=curr_img
        )

        return {
            "title": result.get("fabrizio_title", title),
            "url": url,
            "raw_date": row.get("raw_date", ""),
            "published_at": row.get("published_at", ""),
            "language": lang,
            "summary": result.get("fabrizio_summary", summary),
            "image_url": best_img,
            "category": cat,
            "source": source,
            "player_name": p_name,
            "from_club": f_club,
            "to_club": t_club,
            "transfer_fee": fee_str,
            "fee_numeric": fee_n,
            "league": cat,
            "national_team": nat,
            "status": st,
            "sentiment": sent,
            "semantic_hash": sem,
            "credibility": cred,
        }

    from concurrent.futures import ThreadPoolExecutor

    row_tuples = list(df.iterrows())
    total = len(row_tuples)
    print(f"🧠 Lancement de l'analyse IA parallèle sur {total} articles avec 25 workers...")

    processed_rows = []
    with ThreadPoolExecutor(max_workers=25) as executor:
        for item in executor.map(_process_one_row, row_tuples):
            if item is not None:
                processed_rows.append(item)

    if not processed_rows:
        return pd.DataFrame()

    df = pd.DataFrame(processed_rows)

    # Déduplication sémantique
    df = deduplicate_dataframe(df)

    print(f"✅ Pipeline V2 terminé: {len(df)} articles uniques enrichis.")
    return df


if __name__ == "__main__":
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    in_path = os.path.join(BASE, "data", "output", "articles_raw.csv")
    out_path = os.path.join(BASE, "data", "output", "organized_articles.csv")
    verified_path = os.path.join(BASE, "data", "output", "verified_articles.csv")

    if os.path.exists(in_path):
        df_raw = pd.read_csv(in_path)
        print(f"📖 Chargement de {len(df_raw)} articles bruts depuis {in_path}...")
        df_organized = process_dataset(df_raw)

        # Filtre de sécurité football
        from src.mercato_nlp import is_football_mercato_article
        keep_mask = []
        for _, row in df_organized.iterrows():
            t = str(row.get("title", ""))
            s = str(row.get("summary", ""))
            src = str(row.get("source", ""))
            keep_mask.append(is_football_mercato_article(t, s, source=src))
        df_organized = df_organized[keep_mask].reset_index(drop=True)

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        df_organized.to_csv(out_path, index=False, encoding="utf-8-sig")
        df_organized.to_csv(verified_path, index=False, encoding="utf-8-sig")
        print(f"✅ Sauvegardé : {len(df_organized)} articles football validés dans {out_path} et {verified_path}")
    else:
        print(f"❌ Fichier d'entrée introuvable : {in_path}")

