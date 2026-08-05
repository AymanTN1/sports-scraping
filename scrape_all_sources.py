#!/usr/bin/env python3
"""
scrape_all_sources.py — Exécute le scraping complet de toutes les sources
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scraper import scrape_all

def main():
    BASE = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(BASE, "data", "output", "articles_test.csv")

    print("\n" + "=" * 80)
    print("⚡ DEMARRAGE DU SCRAPING MULTI-SOURCES — SPORTPULSE")
    print("=" * 80)

    try:
        df = scrape_all(output_path, delay=2.0)
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ FINAL DU SCRAPING")
        print("=" * 80)
        total = len(df) if df is not None else 0
        print(f"✅ Total articles trouvés et sauvegardés: {total}")
        print(f"📁 Fichier généré: {output_path}")
    except Exception as exc:
        print(f"\n❌ Erreur pendant le scraping: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
