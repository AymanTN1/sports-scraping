#!/usr/bin/env python3
"""
wrapper_scraper.py — Basculer entre les différentes méthodes de scraping
Permet de tester toutes les implémentations facilement
"""

import sys
import os
import time

def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    SÉLECTEUR DE MÉTHODE DE SCRAPING                        ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    methods = {
        "1": {
            "name": "BeautifulSoup (actuel)",
            "file": "scrape_all_sources.py",
            "cmd": "python scrape_all_sources.py",
            "perf": "0.79s/page",
            "js": "❌",
        },
        "2": {
            "name": "LXML (recommandé) ⚡",
            "file": "src/scraper_lxml.py",
            "cmd": "python src/scraper_lxml.py",
            "perf": "0.25s/page (3.1x plus rapide)",
            "js": "❌",
        },
        "3": {
            "name": "Requests-HTML (hybrid)",
            "file": "src/scraper_requests_html.py",
            "cmd": "python src/scraper_requests_html.py",
            "perf": "0.5-2s/page",
            "js": "✅ (optionnel)",
        },
        "4": {
            "name": "Playwright (JavaScript)",
            "file": "src/scraper_playwright.py",
            "cmd": "python src/scraper_playwright.py",
            "perf": "2-5s/page",
            "js": "✅ (complet)",
        },
        "5": {
            "name": "Comparer les performances",
            "file": "compare_scrapers.py",
            "cmd": "python compare_scrapers.py",
            "perf": "N/A",
            "js": "N/A",
        },
        "0": {
            "name": "Voir le guide",
            "file": "GUIDE_SCRAPING.py",
            "cmd": "python GUIDE_SCRAPING.py",
            "perf": "N/A",
            "js": "N/A",
        },
    }
    
    print("Choisissez une méthode de scraping:\n")
    for key, info in methods.items():
        print(f"  [{key}] {info['name']}")
        print(f"      Fichier: {info['file']}")
        print(f"      Performance: {info['perf']}")
        print(f"      JS Support: {info['js']}")
        print()
    
    choice = input("Votre choix (0-5): ").strip()
    
    if choice not in methods:
        print("❌ Choix invalide")
        return
    
    method = methods[choice]
    print(f"\n🚀 Lancement: {method['name']}")
    print(f"📁 Fichier: {method['file']}")
    print(f"⚡ Performance: {method['perf']}\n")
    print("-" * 80)
    
    os.system(method["cmd"])

if __name__ == "__main__":
    main()
