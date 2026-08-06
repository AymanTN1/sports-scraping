#!/usr/bin/env python3
"""
populate_mercato_db.py — Re-crée et peuple la base de données SQLite MercatoPulse
avec les actualités et transferts en temps réel et historiques.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.db import engine, Base, SessionLocal
from backend.models import Article, Source
from src.scraper import scrape_all_sources
from src.ai_organizer import process_dataset
from src.source_verifier import calculate_source_credibility


def reset_and_populate():
    print("🔄 Suppression et recréation des tables DB MercatoPulse...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    print("🌐 Lancement du Scraper Mercato & Entités NLP...")
    df = scrape_all_sources()
    if df.empty:
        print("⚠️ Aucune donnée retournée par le scraper.")
        return

    df = process_dataset(df)

    db = SessionLocal()
    try:
        source_cache = {}

        inserted = 0
        for _, row in df.iterrows():
            src_name = str(row.get("source", "Source inconnue"))
            if src_name not in source_cache:
                src_obj = db.query(Source).filter_by(name=src_name).first()
                if not src_obj:
                    cred_val = calculate_source_credibility(src_name)
                    src_obj = Source(name=src_name, credibility_score=cred_val)
                    db.add(src_obj)
                    db.flush()
                source_cache[src_name] = src_obj

            source_obj = source_cache[src_name]

            ext_key = str(row.get("external_key", ""))
            if not ext_key:
                continue

            article = Article(
                external_key=ext_key,
                title=str(row.get("title", "")),
                url=str(row.get("url", "")),
                raw_date=str(row.get("raw_date", "")),
                language=str(row.get("language", "fr")),
                category=str(row.get("category", "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿")),
                league=str(row.get("league", "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿")),
                sentiment=str(row.get("sentiment", "Neutre")),
                player_name=str(row.get("player_name", "Joueur Target")),
                from_club=str(row.get("from_club", "Club Vendeur")),
                to_club=str(row.get("to_club", "Club Cible")),
                transfer_fee=str(row.get("transfer_fee", "Non communiqué")),
                status=str(row.get("status", "RUMEUR 📰")),
                summary=str(row.get("summary", "")),
                image_url=str(row.get("image_url", "")),
                credibility_score=float(source_obj.credibility_score or 4.5),
                source_id=source_obj.id,
            )
            db.add(article)
            inserted += 1

        db.commit()
        print(f"✅ DB MercatoPulse initialisée avec succès ! ({inserted} transferts & news enregistrés).")
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors du peuplement DB: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    reset_and_populate()
