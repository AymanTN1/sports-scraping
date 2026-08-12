"""
photo_enricher.py - Module de scraping et enrichissement ultra-rapide des photos pour MercatoPULSE.
1. Extraction directe OpenGraph / Twitter Cards pour les articles web directs.
2. Wikipedia PageImages API haute résolution (600px+) pour les joueurs et entraîneurs.
3. TheSportsDB Cutouts & Renderings transparents.
4. Logos HD officiels des clubs en fallback.
5. Cache persistant sur disque (data/cache/photo_cache.json).
"""

import json
import logging
import os
import re
import sqlite3
import threading
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_FILE = BASE_DIR / "data" / "cache" / "photo_cache.json"
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "MercatoPulseApp/2.0 (https://mercatopulse.live; contact@mercatopulse.live) requests/2.31.0"
}

# ── Base de logos HD pour les clubs majeurs ──
CLUB_BADGES: Dict[str, str] = {
    "Manchester City": "https://upload.wikimedia.org/wikipedia/en/thumb/e/eb/Manchester_City_FC_badge.svg/500px-Manchester_City_FC_badge.svg.png",
    "Barcelona": "https://upload.wikimedia.org/wikipedia/en/thumb/4/47/FC_Barcelona_%28crest%29.svg/500px-FC_Barcelona_%28crest%29.svg.png",
    "FC Barcelone": "https://upload.wikimedia.org/wikipedia/en/thumb/4/47/FC_Barcelona_%28crest%29.svg/500px-FC_Barcelona_%28crest%29.svg.png",
    "Real Madrid": "https://upload.wikimedia.org/wikipedia/en/thumb/5/56/Real_Madrid_CF.svg/500px-Real_Madrid_CF.svg.png",
    "Liverpool": "https://upload.wikimedia.org/wikipedia/en/thumb/0/0c/Liverpool_FC.svg/500px-Liverpool_FC.svg.png",
    "Arsenal": "https://upload.wikimedia.org/wikipedia/en/thumb/5/53/Arsenal_FC.svg/500px-Arsenal_FC.svg.png",
    "Chelsea": "https://upload.wikimedia.org/wikipedia/en/thumb/c/cc/Chelsea_FC.svg/500px-Chelsea_FC.svg.png",
    "Manchester United": "https://upload.wikimedia.org/wikipedia/en/thumb/7/7a/Manchester_United_FC_crest.svg/500px-Manchester_United_FC_crest.svg.png",
    "Paris Saint-Germain": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a7/Paris_Saint-Germain_F.C..svg/500px-Paris_Saint-Germain_F.C..svg.png",
    "PSG": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a7/Paris_Saint-Germain_F.C..svg/500px-Paris_Saint-Germain_F.C..svg.png",
    "Bayern Munich": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/FC_Bayern_M%C3%BCnchen_logo_%282017%29.svg/500px-FC_Bayern_M%C3%BCnchen_logo_%282017%29.svg.png",
    "Juventus": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/Juventus_FC_2017_icon_%28black%29.svg/500px-Juventus_FC_2017_icon_%28black%29.svg.png",
    "Inter Milan": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/FC_Internazionale_Milano_2021.svg/500px-FC_Internazionale_Milano_2021.svg.png",
    "AC Milan": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Logo_of_AC_Milan.svg/500px-Logo_of_AC_Milan.svg.png",
    "Atletico Madrid": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f4/Atletico_Madrid_2017_logo.svg/500px-Atletico_Madrid_2017_logo.svg.png",
    "Atlético de Madrid": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f4/Atletico_Madrid_2017_logo.svg/500px-Atletico_Madrid_2017_logo.svg.png",
    "Tottenham": "https://upload.wikimedia.org/wikipedia/en/thumb/b/b4/Tottenham_Hotspur.svg/500px-Tottenham_Hotspur.svg.png",
    "Newcastle": "https://upload.wikimedia.org/wikipedia/en/thumb/5/56/Newcastle_United_Logo.svg/500px-Newcastle_United_Logo.svg.png",
    "Aston Villa": "https://upload.wikimedia.org/wikipedia/en/thumb/9/9f/Aston_Villa_logo.svg/500px-Aston_Villa_logo.svg.png",
    "Sporting CP": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e1/Sporting_Clube_de_Portugal_%28Logo%29.svg/500px-Sporting_Clube_de_Portugal_%28Logo%29.svg.png",
    "Benfica": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a2/SL_Benfica_logo.svg/500px-SL_Benfica_logo.svg.png",
    "SL Benfica": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a2/SL_Benfica_logo.svg/500px-SL_Benfica_logo.svg.png",
    "Porto": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f1/FC_Porto.svg/500px-FC_Porto.svg.png",
    "FC Porto": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f1/FC_Porto.svg/500px-FC_Porto.svg.png",
    "Napoli": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/SSC_Napoli_2024_%28deep_blue_navy%29.svg/500px-SSC_Napoli_2024_%28deep_blue_navy%29.svg.png",
    "AS Roma": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f7/AS_Roma_logo_%282017%29.svg/500px-AS_Roma_logo_%282017%29.svg.png",
    "Roma": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f7/AS_Roma_logo_%282017%29.svg/500px-AS_Roma_logo_%282017%29.svg.png",
    "SS Lazio": "https://upload.wikimedia.org/wikipedia/en/thumb/c/ce/S.S._Lazio_badge.svg/500px-S.S._Lazio_badge.svg.png",
    "Lazio": "https://upload.wikimedia.org/wikipedia/en/thumb/c/ce/S.S._Lazio_badge.svg/500px-S.S._Lazio_badge.svg.png",
    "Dortmund": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Borussia_Dortmund_logo.svg/500px-Borussia_Dortmund_logo.svg.png",
    "Borussia Dortmund": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Borussia_Dortmund_logo.svg/500px-Borussia_Dortmund_logo.svg.png",
    "Leverkusen": "https://upload.wikimedia.org/wikipedia/en/thumb/5/59/Bayer_04_Leverkusen_logo.svg/500px-Bayer_04_Leverkusen_logo.svg.png",
    "Bayer Leverkusen": "https://upload.wikimedia.org/wikipedia/en/thumb/5/59/Bayer_04_Leverkusen_logo.svg/500px-Bayer_04_Leverkusen_logo.svg.png",
    "RB Leipzig": "https://upload.wikimedia.org/wikipedia/en/thumb/0/04/RB_Leipzig_2020_logo.svg/500px-RB_Leipzig_2020_logo.svg.png",
    "Marseille": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Olympique_de_Marseille_logo.svg/500px-Olympique_de_Marseille_logo.svg.png",
    "Olympique de Marseille": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Olympique_de_Marseille_logo.svg/500px-Olympique_de_Marseille_logo.svg.png",
    "Lyon": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c6/Olympique_Lyonnais.svg/500px-Olympique_Lyonnais.svg.png",
    "Olympique Lyonnais": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c6/Olympique_Lyonnais.svg/500px-Olympique_Lyonnais.svg.png",
    "AS Monaco": "https://upload.wikimedia.org/wikipedia/en/thumb/b/ba/AS_Monaco_FC.svg/500px-AS_Monaco_FC.svg.png",
    "Monaco": "https://upload.wikimedia.org/wikipedia/en/thumb/b/ba/AS_Monaco_FC.svg/500px-AS_Monaco_FC.svg.png",
    "Al-Hilal": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f6/Al-Hilal_Saudi_Club_logo.svg/500px-Al-Hilal_Saudi_Club_logo.svg.png",
    "Al-Nassr": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c5/Al_Nassr_FC_Logo.svg/500px-Al_Nassr_FC_Logo.svg.png",
    "Al-Ittihad": "https://upload.wikimedia.org/wikipedia/en/thumb/5/50/Al-Ittihad_Club_%28Jeddah%29_logo.svg/500px-Al-Ittihad_Club_%28Jeddah%29_logo.svg.png",
    "Al-Ahli": "https://upload.wikimedia.org/wikipedia/en/thumb/b/b8/Al-Ahli_Saudi_FC_logo.svg/500px-Al-Ahli_Saudi_FC_logo.svg.png",
    "Galatasaray": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Galatasaray_Sports_Club_Logo.svg/500px-Galatasaray_Sports_Club_Logo.svg.png",
    "Fenerbahçe": "https://upload.wikimedia.org/wikipedia/en/thumb/3/39/Fenerbah%C3%A7e_SK_logo.svg/500px-Fenerbah%C3%A7e_SK_logo.svg.png",
    "Beşiktaş": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Besiktas_JK_logo.svg/500px-Besiktas_JK_logo.svg.png",
    "Trabzonspor": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a3/Trabzonspor_Amblemi.png/500px-Trabzonspor_Amblemi.png",
    "LA Galaxy": "https://upload.wikimedia.org/wikipedia/en/thumb/7/70/Los_Angeles_Galaxy_logo.svg/500px-Los_Angeles_Galaxy_logo.svg.png",
    "Los Angeles Galaxy": "https://upload.wikimedia.org/wikipedia/en/thumb/7/70/Los_Angeles_Galaxy_logo.svg/500px-Los_Angeles_Galaxy_logo.svg.png",
    "Inter Miami": "https://upload.wikimedia.org/wikipedia/en/thumb/5/5c/Inter_Miami_CF_logo.svg/500px-Inter_Miami_CF_logo.svg.png",
    "San Diego FC": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c2/San_Diego_FC_logo.svg/500px-San_Diego_FC_logo.svg.png",
    "Real Sociedad": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f1/Real_Sociedad_logo.svg/500px-Real_Sociedad_logo.svg.png",
    "Villarreal": "https://upload.wikimedia.org/wikipedia/en/thumb/7/70/Villarreal_CF_logo.svg/500px-Villarreal_CF_logo.svg.png",
    "Athletic Bilbao": "https://upload.wikimedia.org/wikipedia/en/thumb/9/98/Club_Athletic_Bilbao_logo.svg/500px-Club_Athletic_Bilbao_logo.svg.png",
}

_cache_lock = threading.Lock()


def load_cache() -> Dict[str, str]:
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache: Dict[str, str]):
    try:
        with _cache_lock:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning("Erreur sauvegarde cache photo: %s", e)


PHOTO_CACHE = load_cache()


def clean_image_url(url: str) -> str:
    """Valide et nettoie une URL d'image."""
    if not url or not isinstance(url, str) or not url.startswith("http"):
        return ""
    
    url_lower = url.lower()
    bad_patterns = [
        "pixel", "tracking", "1x1", "spacer", "blank.gif",
        "favicon", "default-avatar", "user_icon", "spinner",
        "badge-placeholder", "no-image", "empty."
    ]
    if any(bp in url_lower for bp in bad_patterns):
        return ""
    
    # Améliorer la résolution des thumbnails Wikimedia
    if "upload.wikimedia.org" in url:
        url = re.sub(r"/\d+px-", "/600px-", url)
    
    return url.strip()


def scrape_article_og_image(url: str, timeout: float = 2.0) -> str:
    """Scrape l'image og:image / twitter:image directement depuis la page de l'article."""
    if not url or not url.startswith("http") or "news.google.com" in url:
        return ""
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, stream=True)
        if not r.ok:
            return ""
        
        content = b""
        for chunk in r.iter_content(8192):
            content += chunk
            if len(content) > 65536:
                break
        
        soup = BeautifulSoup(content, "html.parser")
        
        # 1. OpenGraph image
        og = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
        if og and og.get("content"):
            img = clean_image_url(og["content"])
            if img:
                return img
        
        # 2. Twitter Card image
        tw = soup.find("meta", property="twitter:image") or soup.find("meta", attrs={"name": "twitter:image"})
        if tw and tw.get("content"):
            img = clean_image_url(tw["content"])
            if img:
                return img
        
    except Exception:
        pass
    
    return ""


def fetch_player_photo_from_web(player_name: str) -> str:
    """Cherche la photo officielle d'un joueur via Wikipedia et TheSportsDB."""
    if not player_name or len(player_name) < 3 or player_name in ["Joueur Mercato", "Joueur Star", "Star"]:
        return ""
    
    clean_name = player_name.strip()
    
    # ── 1. Wikipedia PageImages API (Ultra Fast & 100% Accurate) ──
    try:
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(clean_name + ' footballer')}&format=json&srlimit=1"
        res = requests.get(search_url, headers=HEADERS, timeout=2.5)
        if res.ok:
            data = res.json()
            search_items = data.get("query", {}).get("search", [])
            if search_items:
                page_title = search_items[0]["title"]
                img_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(page_title)}&prop=pageimages&format=json&pithumbsize=600"
                img_res = requests.get(img_url, headers=HEADERS, timeout=2.5)
                if img_res.ok:
                    pages = img_res.json().get("query", {}).get("pages", {})
                    for _, pdata in pages.items():
                        if "thumbnail" in pdata and pdata["thumbnail"].get("source"):
                            img = clean_image_url(pdata["thumbnail"]["source"])
                            if img:
                                return img
    except Exception:
        pass
    
    # ── 2. TheSportsDB API Cutout / Thumb ──
    try:
        tsdb_url = f"https://www.thesportsdb.com/api/v1/json/3/searchplayers.php?p={urllib.parse.quote(clean_name)}"
        r = requests.get(tsdb_url, headers=HEADERS, timeout=2.0)
        if r.ok:
            players = r.json().get("player") or []
            if players:
                p = players[0]
                img = p.get("strCutout") or p.get("strThumb") or p.get("strRender")
                if img and img.startswith("http"):
                    return clean_image_url(img)
    except Exception:
        pass

    # ── 3. Web Search & Wikipedia Summary Fallback (Ultra Robuste) ──
    try:
        from src.web_resolver import search_web_player_info
        info = search_web_player_info(clean_name)
        if info and info.get("photo"):
            return clean_image_url(info["photo"])
    except Exception:
        pass
    
    return ""


def get_club_badge(club_name: str) -> str:
    """Retourne le logo HD d'un club s'il est reconnu."""
    if not club_name:
        return ""
    for known_club, badge_url in CLUB_BADGES.items():
        if known_club.lower() in club_name.lower():
            return badge_url
    return ""


def resolve_photo_for_article(
    article_url: str = "",
    player_name: str = "",
    to_club: str = "",
    from_club: str = "",
    current_image: str = ""
) -> str:
    """
    Résout la meilleure photo possible pour un article en utilisant l'ordre de priorité :
    1. Photo existante déjà valide
    2. Photo officielle du joueur / entraîneur (avec cache persistent)
    3. Scraping direct og:image sur la page
    4. Logo officiel du club acheteur ou vendeur
    5. Recherche Wikipedia logo club en fallback
    """
    # 1. Image courante valide
    valid_current = clean_image_url(current_image)
    if valid_current:
        return valid_current
    
    # Nettoyage des noms
    p_clean = (player_name or "").strip()
    if p_clean in ["Joueur Mercato", "Joueur Star", "Star", "nan", "None"]:
        p_clean = ""

    # 2. Photo Joueur / Entraîneur via cache / web
    if p_clean and len(p_clean) >= 3:
        cache_key = f"player:{p_clean.lower()}"
        with _cache_lock:
            cached = PHOTO_CACHE.get(cache_key)
        if cached:
            return cached
        
        photo = fetch_player_photo_from_web(p_clean)
        if photo:
            with _cache_lock:
                PHOTO_CACHE[cache_key] = photo
                save_cache(PHOTO_CACHE)
            return photo

    # 3. Logo Club (Acheteur prioritaire, puis Vendeur)
    for c_candidate in [to_club, from_club]:
        if not c_candidate or c_candidate in ["Club Acheteur", "Club Vendeur", "Club Cible", "Club Acquéreur", "nan"]:
            continue
        c_clean = c_candidate.strip()
        cache_key = f"badge:{c_clean.lower()}"
        with _cache_lock:
            cached = PHOTO_CACHE.get(cache_key)
        if cached:
            return cached
        
        badge = get_club_badge(c_clean)
        if badge:
            with _cache_lock:
                PHOTO_CACHE[cache_key] = badge
                save_cache(PHOTO_CACHE)
            return badge
        
        # Tentative recherche logo club via web Wikipedia
        badge_web = fetch_player_photo_from_web(f"{c_clean} FC")
        if badge_web:
            with _cache_lock:
                PHOTO_CACHE[cache_key] = badge_web
                save_cache(PHOTO_CACHE)
            return badge_web

    # 4. Scraping og:image direct de l'article si URL valide
    if article_url and article_url.startswith("http") and "news.google.com" not in article_url:
        page_img = scrape_article_og_image(article_url)
        if page_img:
            return page_img

    return ""


def enrich_database_photos(db_path: Optional[Path] = None, max_workers: int = 20) -> int:
    """
    Parcourt la base de données SQLite et enrichit tous les articles sans photo.
    """
    if db_path is None:
        db_path = BASE_DIR / "data" / "sportpulse.db"
    
    if not db_path.exists():
        db_path = BASE_DIR / "sportpulse.db"
        if not db_path.exists():
            logger.warning("Base SQLite introuvable à %s", db_path)
            return 0
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, url, player_name, to_club, from_club, image_url 
        FROM articles
    """)
    rows = cursor.fetchall()
    
    logger.info("Analyse de %d articles pour enrichissement photos...", len(rows))
    
    updates_to_run = []
    
    def process_row(row):
        art_id, url, player, to_c, from_c, cur_img = row
        cur_img = cur_img or ""
        if cur_img and cur_img.startswith("http") and not any(bad in cur_img.lower() for bad in ["pixel", "spacer", "blank"]):
            return None
        
        best_img = resolve_photo_for_article(
            article_url=url or "",
            player_name=player or "",
            to_club=to_c or "",
            from_club=from_c or "",
            current_image=cur_img
        )
        if best_img and best_img != cur_img:
            return (best_img, art_id)
        return None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_row, row): row for row in rows}
        for future in as_completed(futures):
            res = future.result()
            if res:
                updates_to_run.append(res)
    
    if updates_to_run:
        cursor.executemany("UPDATE articles SET image_url = ? WHERE id = ?", updates_to_run)
        conn.commit()
        updated_count = len(updates_to_run)
        logger.info("✅ %d articles mis à jour avec des photos officielles dans SQLite !", updated_count)
    else:
        updated_count = 0
        logger.info("Toutes les photos sont déjà à jour.")
    
    conn.close()
    save_cache(PHOTO_CACHE)
    return updated_count


def enrich_csv_photos(csv_path: Path, max_workers: int = 20) -> None:
    """Enrichit un fichier CSV avec les photos scrapées."""
    if not csv_path.exists():
        return
    
    import pandas as pd
    try:
        df = pd.read_csv(csv_path)
        if "player_name" not in df.columns:
            return
        
        if "image_url" not in df.columns:
            df["image_url"] = ""
        
        updated = 0
        for idx, row in df.iterrows():
            cur_img = str(row.get("image_url", "")).strip()
            if cur_img and cur_img != "nan" and cur_img.startswith("http"):
                continue
            
            p_name = str(row.get("player_name", ""))
            to_c = str(row.get("to_club", ""))
            from_c = str(row.get("from_club", ""))
            url = str(row.get("url", ""))
            
            photo = resolve_photo_for_article(
                article_url=url,
                player_name=p_name,
                to_club=to_c,
                from_club=from_c,
                current_image=""
            )
            if photo:
                df.at[idx, "image_url"] = photo
                updated += 1
        
        df.to_csv(csv_path, index=False)
        logger.info("CSV %s enrichi avec %d photos", csv_path.name, updated)
    except Exception as e:
        logger.warning("Erreur enrichissement CSV %s: %s", csv_path.name, e)


if __name__ == "__main__":
    logger.info("🚀 Démarrage du scraping global des photos Mercato...")
    updated = enrich_database_photos()
    
    output_dir = BASE_DIR / "data" / "output"
    for fname in ["articles_raw.csv", "organized_articles.csv", "verified_articles.csv", "articles.csv"]:
        enrich_csv_photos(output_dir / fname)
    
    logger.info("🎉 Scraping des photos terminé avec succès !")
