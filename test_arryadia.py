#!/usr/bin/env python3
from src.scraper import scrape_source

# Tester juste Arryadia
arryadia = {
    'name': 'Arryadia',
    'url': 'https://arryadia.com/',
    'lang': 'ar',
    'selectors': {
        'articles': 'article, .post, .item, .news, .story, .entry, div[class*="post"], div[class*="article"], li[class*="post"], li[class*="article"]',
        'title': 'h2, h3, h1, .title, .post-title, .article-title, .headline, span[class*="title"]',
        'link': 'a[href], .link a',
        'date': 'time, .date, .time, .posted-on, span[class*="date"], span[class*="time"]',
    },
}

print("=" * 80)
print("TEST SCRAPING ARRYADIA")
print("=" * 80)

articles = scrape_source(arryadia, retries=3)
print(f'\n✅ {len(articles)} articles trouvés\n')

if articles:
    print("Premiers articles:")
    for i, a in enumerate(articles[:5]):
        print(f'\n{i+1}. Titre: {a["title"][:70]}')
        print(f'   Source: {a["source"]}')
        print(f'   URL: {a["url"][:70]}')
        print(f'   Date: {a["date"]}')
else:
    print("❌ Aucun article trouvé pour Arryadia")
