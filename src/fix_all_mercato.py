"""
fix_all_mercato.py — Ré-analyse complète et enrichissement de toute la base SQLite et des CSV.
1. Applique le nouveau moteur NLP Mercato (correction inversions, détection clubs vendeur/acheteur).
2. Enrichit chaque article avec sa vraie photo officielle HD.
3. Met à jour SQLite (sportpulse.db) et les fichiers CSV.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import logging
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from src.mercato_nlp import parse_article_full
from src.photo_enricher import resolve_photo_for_article

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "sportpulse.db"


def fix_sqlite():
    if not DB_PATH.exists():
        logger.warning("DB introuvable : %s", DB_PATH)
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, summary, player_name, from_club, to_club, status, image_url, url 
        FROM articles
    """)
    rows = cursor.fetchall()
    logger.info("Traitement de %d articles en base SQLite...", len(rows))

    updates = []

    def process_article(row):
        art_id, title, summary, cur_p, cur_from, cur_to, cur_stat, cur_img, url = row
        title = title or ""
        summary = summary or ""

        # 1. NLP Parse
        nlp_res = parse_article_full(title, summary)
        new_player = nlp_res["player_name"]
        new_from = nlp_res["from_club"]
        new_to = nlp_res["to_club"]
        new_stat = nlp_res["status"]

        # 2. Photo Resolve
        best_img = resolve_photo_for_article(
            article_url=url or "",
            player_name=new_player,
            to_club=new_to,
            from_club=new_from,
            current_image=cur_img or "",
        )

        return (new_player, new_from, new_to, new_stat, best_img, art_id)

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(process_article, row): row for row in rows}
        for f in as_completed(futures):
            res = f.result()
            if res:
                updates.append(res)

    cursor.executemany("""
        UPDATE articles 
        SET player_name = ?, from_club = ?, to_club = ?, status = ?, image_url = ?
        WHERE id = ?
    """, updates)

    conn.commit()
    conn.close()
    logger.info("✅ %d articles SQLite mis à jour avec succès !", len(updates))


def fix_csvs():
    csv_files = [
        BASE_DIR / "data" / "output" / "organized_articles.csv",
        BASE_DIR / "data" / "output" / "verified_articles.csv",
        BASE_DIR / "data" / "articles_raw.csv",
    ]

    for csv_file in csv_files:
        if not csv_file.exists():
            continue
        try:
            df = pd.read_csv(csv_file)
            if df.empty:
                continue

            for idx, row in df.iterrows():
                title = str(row.get("title", ""))
                summary = str(row.get("summary", ""))
                url = str(row.get("url", ""))
                cur_img = str(row.get("image_url", ""))

                nlp_res = parse_article_full(title, summary)
                p = nlp_res["player_name"]
                f_c = nlp_res["from_club"]
                t_c = nlp_res["to_club"]
                st = nlp_res["status"]

                best_img = resolve_photo_for_article(
                    article_url=url,
                    player_name=p,
                    to_club=t_c,
                    from_club=f_c,
                    current_image=cur_img,
                )

                df.at[idx, "player_name"] = p
                df.at[idx, "from_club"] = f_c
                df.at[idx, "to_club"] = t_c
                df.at[idx, "status"] = st
                if best_img:
                    df.at[idx, "image_url"] = best_img

            df.to_csv(csv_file, index=False)
            logger.info("✅ CSV %s mis à jour avec succès !", csv_file.name)
        except Exception as e:
            logger.error("Erreur sur %s: %s", csv_file, e)


if __name__ == "__main__":
    fix_sqlite()
    fix_csvs()
