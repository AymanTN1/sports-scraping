#!/usr/bin/env python3
"""
ai_enhancer.py — Module d'enrichissement IA & Mise en forme Fabrizio Romano Style pour MercatoPULSE.

Fonctionnalités :
1. Mise en forme automatique des annonces au style emblématique de Fabrizio Romano :
   - Badges d'impact : 🚨 HERE WE GO!, 🚨 BREAKING:, 🔒 CONFIDENTIAL, 💎 EXCLUSIVE, ✅ OFFICIEL
   - Structure à puces : Accord verbal, Montant (€), Visite médicale, Contrat.
   - Tagline interactive : "Rate this signing from 1 to 10! ⏬"
2. Support hybride :
   - Si GROQ_API_KEY, OPENAI_API_KEY ou OPENROUTER_API_KEY est disponible, utilise un LLM via API.
   - Sinon, utilise un moteur de règles NLP local ultra-précis (0 € de coût).
"""
from __future__ import annotations

import os
import re
import sys
from typing import Dict, Optional

# Assurer l'importation depuis la racine
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mercato_nlp import clean_text_norm, parse_article_full


def format_fabrizio_romano_style_local(article: Dict[str, str]) -> Dict[str, str]:
    """
    Génère un résumé et un titre au style Fabrizio Romano en utilisant le moteur NLP local.
    """
    title = str(article.get("title", "")).strip()
    summary = str(article.get("summary", "")).strip()
    player = str(article.get("player_name", "") or "").strip()
    from_c = str(article.get("from_club", "") or "").strip()
    to_c = str(article.get("to_club", "") or "").strip()
    status = str(article.get("status", "") or "RUMEUR 📰").strip().upper()
    fee = str(article.get("transfer_fee", "") or "Non communiqué").strip()
    
    if player in ["Joueur Mercato", "Joueur Star", "Star", "nan", ""]:
        player = ""
    if from_c in ["Club Vendeur", "Club Acquéreur", "nan"]:
        from_c = ""
    if to_c in ["Club Acheteur", "Club Cible", "nan"]:
        to_c = ""

    # Déterminer l'entête Fabrizio Romano
    if "OFFICIEL" in status or "CONFIRMED" in status:
        header = "🚨 OFFICIEL / CONFIRMED"
        badge = "OFFICIEL ✅"
    elif "HERE WE GO" in status:
        header = "🚨 HERE WE GO!"
        badge = "HERE WE GO 🔥"
    elif "NEGOCIATION" in status or "TALKS" in status or "ADVANCED" in status:
        header = "🚨 CONFIDENTIAL & ADVANCED TALKS"
        badge = "CONFIDENTIAL 🔒"
    else:
        header = "🚨 BREAKING / EXCLUSIVE"
        badge = "EXCLUSIVE 💎"

    # Construction du titre Fabrizio
    if player and to_c and from_c and from_c != to_c:
        fab_title = f"{header}: {player} to {to_c} from {from_c} — {fee}"
    elif player and to_c:
        fab_title = f"{header}: {player} set to join {to_c}"
    elif player:
        fab_title = f"{header}: {player} transfer updates"
    else:
        fab_title = f"{header}: {title}"

    # Construction de la description Fabrizio Romano
    bullets = []
    if player and to_c:
        bullets.append(f"🚨 {header}: {to_c} have reached agreement for {player}.")
    elif player:
        bullets.append(f"🚨 {header}: Major update on {player}'s future.")
    else:
        bullets.append(f"🚨 {header}: {title}")

    if from_c and to_c and from_c != to_c:
        bullets.append(f"🤝 Formal steps ongoing between {from_c} and {to_c}.")
    elif from_c == to_c and from_c:
        bullets.append(f"📝 Contract extension agreed with {from_c}.")

    if fee and fee != "Non communiqué":
        bullets.append(f"💶 Fee agreed around {fee} plus bonus & add-ons.")

    bullets.append("🩺 Medical tests scheduled and personal terms agreed.")
    bullets.append("💬 Rate this signing from 1 to 10! ⏬")

    fab_summary = "\n\n".join(bullets)

    res = dict(article)
    res["fabrizio_title"] = fab_title
    res["fabrizio_summary"] = fab_summary
    res["fabrizio_badge"] = badge
    return res


def format_fabrizio_romano_ai(article: Dict[str, str]) -> Dict[str, str]:
    """
    Appelle une API IA (Groq / OpenAI / OpenRouter) si une clé est disponible.
    """
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return format_fabrizio_romano_style_local(article)

    # Importer requests de façon sécurisée
    try:
        import requests
        
        prompt = f"""You are Fabrizio Romano, the world's #1 football transfer journalist.
Reformat the following football transfer news into your iconic Instagram/Twitter post format.

Original Title: {article.get('title')}
Original Summary: {article.get('summary')}
Player: {article.get('player_name')}
From Club: {article.get('from_club')}
To Club: {article.get('to_club')}
Status: {article.get('status')}

Rules:
1. Start with '🚨 HERE WE GO!' or '🚨 BREAKING:' or '🚨 CONFIDENTIAL:'
2. Use bullet points with emojis (🤝, 💶, 🩺, 📝, 💬).
3. End with 'Rate this transfer from 1 to 10! ⏬'
4. Keep it concise, high-energy, and accurate.
Return JSON with keys: 'title', 'summary', 'badge'
"""
        
        if os.getenv("GROQ_API_KEY"):
            url = "https://api.groq.com/openai/v1/chat/completions"
            model = "llama-3.3-70b-versatile"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        else:
            url = "https://api.openai.com/v1/chat/completions"
            model = "gpt-4o-mini"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.3
        }

        r = requests.post(url, headers=headers, json=payload, timeout=6)
        if r.ok:
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            import json
            parsed = json.loads(content)
            res = dict(article)
            res["fabrizio_title"] = parsed.get("title", article.get("title"))
            res["fabrizio_summary"] = parsed.get("summary", article.get("summary"))
            res["fabrizio_badge"] = parsed.get("badge", article.get("status", "HERE WE GO 🔥"))
            return res
    except Exception:
        pass

    return format_fabrizio_romano_style_local(article)
