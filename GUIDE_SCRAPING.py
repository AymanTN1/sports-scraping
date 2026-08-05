#!/usr/bin/env python3
"""
GUIDE COMPLET: 6 MÉTHODES DE WEB SCRAPING
===========================================

Vous avez créé 3 implémentations de scraping. Voici comment les utiliser.
"""

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    6 MÉTHODES DE WEB SCRAPING EN PYTHON                    ║
╚════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 MÉTHODE 1: BEAUTIFULSOUP + REQUESTS (ACTUEL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   📁 Fichier: src/scraper.py

   ✅ Avantages:
      • Simple et lisible
      • Excellent pour débuter
      • Bonne communauté
      • CSS selectors intuitifs

   ❌ Inconvénients:
      • Plus lent que LXML
      • Pas de rendu JavaScript
      • CSS selectors complexes difficiles

   ⚡ Performance: 0.79s par page
   
   🎯 Cas d'usage:
      • Sites HTML simples
      • Prototypage rapide
      • Petits projets

   🔧 Installation: pip install beautifulsoup4 requests
   
   💻 Utilisation:
      python -c "from src.scraper import scrape_all; scrape_all('output.csv')"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 MÉTHODE 2: LXML (⚡ PLUS RAPIDE - RECOMMANDÉ)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   📁 Fichier: src/scraper_lxml.py

   ✅ Avantages:
      • ⚡ 3.1x PLUS RAPIDE que BeautifulSoup
      • XPath très puissant
      • Parser C natif (ultra-rapide)
      • Léger en ressources
      • Parfait pour gros volumes

   ❌ Inconvénients:
      • XPath moins intuitif que CSS
      • Pas de rendu JavaScript
      • Courbe d'apprentissage XPath

   ⚡ Performance: 0.25s par page (gain 68% vs BeautifulSoup)
   
   🎯 Cas d'usage:
      • Projets performance-critical
      • Gros volumes de scraping
      • Sites statiques complexes
      • Données haute fréquence

   🔧 Installation: pip install lxml
   
   💻 Utilisation:
      python src/scraper_lxml.py

   📚 Exemples XPath:
      "//article"                    → tous les <article>
      "//div[@class='post']"         → div avec class="post"
      ".//h2/following-sibling::p"   → p après h2
      "//article[1]"                 → premier article
      "//a/@href"                    → tous les href

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 MÉTHODE 3: REQUESTS-HTML (Hybrid)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   📁 Fichier: src/scraper_requests_html.py

   ✅ Avantages:
      • Syntaxe CSS + XPath combinées
      • JavaScript rendering optionnel
      • Plus simple que BeautifulSoup
      • Bon équilibre rapidité/fonctionnalités

   ❌ Inconvénients:
      • JS rendering plus lent
      • Moins mature que BeautifulSoup
      • Documentation limitée

   ⚡ Performance: 0.5-2s (selon JS)
   
   🎯 Cas d'usage:
      • Sites avec JS modéré
      • Besoin CSS et XPath
      • Flexibilité + rapidité

   🔧 Installation: pip install requests-html
   
   💻 Utilisation:
      python src/scraper_requests_html.py

   📚 Exemple:
      # Sans JS
      r = session.get(url)
      articles = r.html.find("article")
      
      # Avec JS rendering
      r = session.get(url)
      r.html.render()  # Rendre JavaScript
      articles = r.html.find("article")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 MÉTHODE 4: PLAYWRIGHT (JavaScript complet)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   📁 Fichier: src/scraper_playwright.py

   ✅ Avantages:
      • Supporte JavaScript complet
      • Multi-navigateur (Chrome/FF/Safari)
      • Fast headless par défaut
      • Interactions (clics, scroll)

   ❌ Inconvénients:
      • Lent (lancement navigateur)
      • Lourd en ressources
      • Overkill pour sites statiques

   ⚡ Performance: 2-5s par page
   
   🎯 Cas d'usage:
      • Sites JavaScript heavy
      • Applications SPA (React, Vue)
      • Interactions complexes
      • Données dynamiques

   🔧 Installation:
      pip install playwright
      playwright install

   💻 Utilisation:
      python src/scraper_playwright.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 MÉTHODE 5: SELENIUM (Classic)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   ✅ Avantages:
      • Très populaire
      • Excellente documentation
      • Interactions complètes
      • Multi-navigateur

   ❌ Inconvénients:
      • TRÈS LENT
      • Lourd en ressources
      • Configuration complexe

   ⚡ Performance: 5-10s par page
   
   🔧 Installation:
      pip install selenium webdriver-manager

   💻 Exemple:
      from selenium import webdriver
      driver = webdriver.Chrome()
      driver.get(url)
      articles = driver.find_elements("css selector", "article")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 MÉTHODE 6: SCRAPY (Framework complet)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   ✅ Avantages:
      • Framework complet
      • Requêtes parallèles
      • Middleware puissant
      • Excellent pour gros projets

   ❌ Inconvénients:
      • Overkill pour petits projets
      • Courbe d'apprentissage importante

   ⚡ Performance: Peut être très rapide avec parallelization
   
   🔧 Installation:
      pip install scrapy

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 TABLEAU COMPARATIF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────┬──────────┬────────────┬──────────┬──────────────┐
│ Méthode          │ Rapidité │ JS Support │ CPU/RAM  │ Facilité     │
├──────────────────┼──────────┼────────────┼──────────┼──────────────┤
│ BeautifulSoup    │ ⭐⭐⭐⭐  │ ❌         │ ⭐⭐     │ ⭐⭐⭐⭐⭐  │
│ LXML             │ ⭐⭐⭐⭐⭐ │ ❌         │ ⭐⭐     │ ⭐⭐⭐⭐   │ ← MEILLEUR
│ Requests-HTML    │ ⭐⭐⭐⭐  │ ✅ (lent)  │ ⭐⭐⭐   │ ⭐⭐⭐⭐   │
│ Playwright       │ ⭐⭐     │ ✅         │ ⭐⭐⭐⭐⭐ │ ⭐⭐⭐    │
│ Selenium         │ ⭐       │ ✅         │ ⭐⭐⭐⭐⭐ │ ⭐⭐⭐    │
│ Scrapy           │ ⭐⭐⭐⭐  │ ❌ (+ JS)  │ ⭐⭐⭐⭐ │ ⭐⭐      │
└──────────────────┴──────────┴────────────┴──────────┴──────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 MATRICE DE DÉCISION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Je veux...                          → Utiliser
─────────────────────────────────────────────────────────────────────
Débuter / prototype                 → BeautifulSoup
Scraper VITE des 1000 pages        → LXML ⚡
Scraper avec du JS modéré          → Requests-HTML
Scraper du JavaScript heavy        → Playwright
Faire du scraping professionnel     → Scrapy
Être compatible avec tous les tests → Selenium


💡 POUR VOTRE PROJET SPORTPULSE ACTUEL:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ RECOMMANDATION: Utiliser LXML

Raison:
   • Vous scrapers des articles statiques (pas de JS)
   • Vous voulez scraper rapidement 14+ sources
   • LXML est 3.1x plus rapide que BeautifulSoup
   • Passer de 0.79s → 0.25s par page = énorme gain
   • Si vous scrapiez 1000 pages: 13min → 4min

Réplace simplement:
   python scrape_all_sources.py
   Par:
   python src/scraper_lxml.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

# Les fichiers créés
print("\n📁 FICHIERS CRÉÉS:")
print("""
   ✅ src/scraper.py                - ACTUEL (BeautifulSoup)
   ✅ src/scraper_lxml.py           - NOUVEAU (LXML ultra-rapide)
   ✅ src/scraper_requests_html.py  - NOUVEAU (Hybrid)
   ✅ src/scraper_playwright.py     - NOUVEAU (JavaScript)
   ✅ METHODES_SCRAPING.txt         - Documentation
   ✅ compare_scrapers.py           - Benchmark
""")
