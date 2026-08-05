#!/usr/bin/env python3
"""
scraper_playwright.py — Scraping avec Playwright
Pour sites avec beaucoup de JavaScript
"""

from playwright.sync_api import sync_playwright
import pandas as pd
import os
import time
from datetime import datetime

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    ),
}

SOURCES = [
    {
        "name": "BBC Sport",
        "url": "https://www.bbc.com/sport",
        "lang": "en",
        "selectors": {
            "articles": "article, .gs-c-promo",
            "title": "h3, h2",
            "link": "a",
        },
    },
    {
        "name": "Sky Sports",
        "url": "https://www.skysports.com/",
        "lang": "en",
        "selectors": {
            "articles": "article, .news-list__item",
            "title": "h2, h3",
            "link": "a",
        },
    },
]


def scrape_with_playwright(source: dict) -> list[dict]:
    """Scrape avec Playwright (avec JavaScript rendering)"""
    articles = []
    
    try:
        print(f"  🎭 {source['name']}…", end="", flush=True)
        
        with sync_playwright() as p:
            # Lancer le navigateur
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Aller à l'URL
            page.goto(source["url"], timeout=15000, wait_until="networkidle")
            
            today = datetime.now().strftime("%Y-%m-%d")
            found_titles = set()
            
            # Attendre que les articles se chargent
            try:
                page.wait_for_selector(source["selectors"]["articles"].split(",")[0].strip(), timeout=5000)
            except:
                pass
            
            # Extraire les articles avec Playwright
            containers = page.query_selector_all(source["selectors"]["articles"])
            
            for container in containers[:30]:
                try:
                    # Titre
                    title_elem = container.query_selector(source["selectors"]["title"])
                    if not title_elem:
                        continue
                    
                    title = title_elem.inner_text().strip()
                    if len(title) < 10 or title in found_titles:
                        continue
                    
                    # URL
                    link_elem = container.query_selector("a")
                    url = ""
                    if link_elem:
                        href = link_elem.get_attribute("href") or ""
                        url = href if href.startswith("http") else source["url"].rstrip("/") + "/" + href.lstrip("/")
                    
                    if title and url:
                        found_titles.add(title)
                        articles.append({
                            "title": title,
                            "source": source["name"],
                            "lang": source["lang"],
                            "url": url,
                            "date": today,
                            "summary": "",
                            "category": "",
                            "credibility": 0,
                        })
                except Exception:
                    pass
            
            browser.close()
        
        print(f" {len(articles)} articles")
        
    except Exception as e:
        print(f" ❌ {str(e)[:40]}")
    
    if not articles:
        print(f" ⚠️ Aucun article")
    
    return articles


def scrape_all_playwright(output_path: str) -> pd.DataFrame:
    """Scrape avec Playwright"""
    all_articles = []
    print(f"\n🎭 Playwright Scraping ({len(SOURCES)} sources)\n")
    
    for i, source in enumerate(SOURCES, 1):
        print(f"[{i}/{len(SOURCES)}]", end=" ")
        articles = scrape_with_playwright(source)
        all_articles.extend(articles)
        
        if i < len(SOURCES):
            time.sleep(2)
    
    df = pd.DataFrame(all_articles)
    if df.empty:
        print("\n⚠️ Aucun article")
        return df
    
    before = len(df)
    df = df.drop_duplicates(subset=["title"])
    after = len(df)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    print(f"\n✅ {after} articles → {output_path}")
    return df


if __name__ == "__main__":
    print("Note: Playwright nécessite les navigateurs installés")
    print("Installation: playwright install")
    
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(BASE, "data", "output", "articles_playwright.csv")
    scrape_all_playwright(out)
