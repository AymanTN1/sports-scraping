"""
web_resolver.py — Résolution automatique Web pour les Joueurs, Photos et Clubs inconnus.
1. Wikipedia Intro Parsing pour détecter le club actuel d'un joueur inconnu.
2. DuckDuckGo / Wikimedia image search fallback pour trouver des photos réelles de n'importe quel joueur/article.
3. Cache local pour garantir une vitesse instantanée.
"""

import json
import logging
import os
import re
import urllib.parse
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_FILE = BASE_DIR / "data" / "cache" / "web_resolver_cache.json"
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def load_resolver_cache() -> Dict[str, dict]:
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_resolver_cache(cache: Dict[str, dict]):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


RESOLVER_CACHE = load_resolver_cache()


def search_web_player_info(player_name: str) -> Dict[str, str]:
    """
    Interroge Wikipedia & le Web pour trouver :
    - Le club actuel du joueur
    - La nationalité
    - Une photo officielle HD
    """
    if not player_name or len(player_name) < 3 or player_name in ["Joueur Mercato", "Joueur Star", "Star"]:
        return {"current_club": "", "nat": "International 🌍", "photo": ""}

    cache_key = player_name.strip().lower()
    if cache_key in RESOLVER_CACHE:
        return RESOLVER_CACHE[cache_key]

    result = {"current_club": "", "nat": "International 🌍", "photo": ""}

    try:
        # 1. Wikipedia Summary API
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(player_name)}"
        r = requests.get(wiki_url, headers=HEADERS, timeout=2.5)
        if r.ok:
            data = r.json()
            extract = data.get("extract", "")
            
            # Photo
            if "thumbnail" in data and data["thumbnail"].get("source"):
                img = data["thumbnail"]["source"]
                img = re.sub(r"/\d+px-", "/600px-", img)
                result["photo"] = img

            # Extraction du club actuel depuis l'intro Wikipedia
            # ex: "is a French professional footballer who plays as a forward for Real Madrid and the France national team."
            club_match = re.search(r"plays\s+(?:as\s+a\s+[\w\s]+)?for\s+(?:the\s+)?(?:Saudi\s+Pro\s+League\s+club\s+|Premier\s+League\s+club\s+|La\s+Liga\s+club\s+|Serie\s+A\s+club\s+|Ligue\s+1\s+club\s+|Bundesliga\s+club\s+|club\s+)?([A-Z][A-Za-z0-9\s\.\-]{2,25}?)(?:\s+and\s+|\s+on\s+loan|\s+as\s+|\.|,)", extract)
            if club_match:
                candidate_club = club_match.group(1).strip()
                if candidate_club and len(candidate_club) > 2 and candidate_club not in ["the", "a", "national team"]:
                    result["current_club"] = candidate_club

    except Exception as e:
        logger.debug("Erreur Wikipedia summary pour %s: %s", player_name, e)

    # 2. DuckDuckGo Image Fallback si pas de photo trouvée
    if not result["photo"]:
        try:
            ddg_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(player_name + ' footballer')}"
            r = requests.get(ddg_url, headers=HEADERS, timeout=2.5)
            if r.ok:
                soup = BeautifulSoup(r.text, "html.parser")
                # Chercher une image dans les résultats
                img_tag = soup.find("img", src=re.compile(r"upload\.wikimedia\.org|thesportsdb|img|photo"))
                if img_tag and img_tag.get("src"):
                    src = img_tag["src"]
                    if src.startswith("//"):
                        src = "https:" + src
                    result["photo"] = src
        except Exception:
            pass

    RESOLVER_CACHE[cache_key] = result
    save_resolver_cache(RESOLVER_CACHE)
    return result
