#!/usr/bin/env python3
"""
compare_scrapers.py — Comparer les différentes méthodes de scraping
"""

import time
import requests
from bs4 import BeautifulSoup
from lxml import html as lxml_html

print("=" * 80)
print("BENCHMARK: COMPARAISON DES MÉTHODES DE SCRAPING")
print("=" * 80)

# Test URL
test_url = "https://www.lequipe.fr/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

print(f"\n🎯 URL test: {test_url}\n")

# ─────────────────────────────────────────────────────────────────────────────
# 1. BEAUTIFULSOUP (métode actuelle)
# ─────────────────────────────────────────────────────────────────────────────
print("1️⃣ BEAUTIFULSOUP (HTML Parser)")
print("-" * 40)

start = time.time()
try:
    resp = requests.get(test_url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")
    articles = soup.select("article, .article")
    bs_time = time.time() - start
    print(f"   ✅ Parsing: {bs_time:.3f}s")
    print(f"   📊 Articles trouvés: {len(articles)}")
except Exception as e:
    print(f"   ❌ Erreur: {str(e)[:50]}")
    bs_time = None

# ─────────────────────────────────────────────────────────────────────────────
# 2. LXML (XPath)
# ─────────────────────────────────────────────────────────────────────────────
print("\n2️⃣ LXML (XPath Parser)")
print("-" * 40)

start = time.time()
try:
    resp = requests.get(test_url, headers=HEADERS, timeout=10)
    tree = lxml_html.fromstring(resp.text)
    articles = tree.xpath("//article | //div[@class='article']")
    lxml_time = time.time() - start
    print(f"   ✅ Parsing: {lxml_time:.3f}s")
    print(f"   📊 Articles trouvés: {len(articles)}")
except Exception as e:
    print(f"   ❌ Erreur: {str(e)[:50]}")
    lxml_time = None

# ─────────────────────────────────────────────────────────────────────────────
# 3. REQUESTS-HTML
# ─────────────────────────────────────────────────────────────────────────────
print("\n3️⃣ REQUESTS-HTML (Syntaxe simple)")
print("-" * 40)

try:
    from requests_html import HTMLSession
    
    start = time.time()
    session = HTMLSession()
    r = session.get(test_url, headers=HEADERS, timeout=10)
    articles = r.html.find("article, .article")
    rhtml_time = time.time() - start
    print(f"   ✅ Parsing: {rhtml_time:.3f}s")
    print(f"   📊 Articles trouvés: {len(articles)}")
except ImportError:
    print(f"   ⚠️  Non installé (pip install requests-html)")
    rhtml_time = None
except Exception as e:
    print(f"   ❌ Erreur: {str(e)[:50]}")
    rhtml_time = None

# ─────────────────────────────────────────────────────────────────────────────
# RÉSUMÉ
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("📊 RÉSUMÉ DES PERFORMANCES")
print("=" * 80)

results = []
if bs_time:
    results.append(("BeautifulSoup", bs_time))
if lxml_time:
    results.append(("LXML", lxml_time))
if rhtml_time:
    results.append(("Requests-HTML", rhtml_time))

if results:
    results.sort(key=lambda x: x[1])
    print()
    for i, (name, timing) in enumerate(results, 1):
        speedup = results[0][1] / timing if timing > 0 else 1
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        print(f"{emoji} {i}. {name:20s}: {timing:.3f}s {'(Base)' if i == 1 else f'({speedup:.1f}x plus rapide)'}")

# ─────────────────────────────────────────────────────────────────────────────
# RECOMMANDATION
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("💡 RECOMMANDATION")
print("=" * 80)

if lxml_time and bs_time and lxml_time < bs_time * 0.8:
    print("\n✅ LXML est nettement plus rapide ➡️ Utiliser scraper_lxml.py")
elif rhtml_time and rhtml_time < bs_time * 0.9:
    print("\n✅ Requests-HTML est compétitif ➡️ Utiliser scraper_requests_html.py")
else:
    print("\n✅ BeautifulSoup est bon ➡️ Continuer avec scraper.py actuel")

print("""
📌 CRITÈRES DE CHOIX:

   • Rapidité maximale        → LXML
   • JS rendering optionnel   → Requests-HTML  
   • JS rendering obligatoire → Playwright
   • Projet simple            → BeautifulSoup (actuellement utilisé)
   • Projet grande échelle    → Scrapy
""")

print("=" * 80)
