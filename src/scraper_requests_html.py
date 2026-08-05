#!/usr/bin/env python3
"""
scraper_requests_html.py — Scraping avec Requests-HTML
Alternative simple avec JS rendering optionnel
"""

from requests_html import HTMLSession
import pandas as pd
import os
import time
import random
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
        "render_js": False,  # Pas besoin de JS
        "selectors": {
            "articles": "article, .gs-c-promo",
            "title": "h3, h2",
            "link": "a",
            "date": "time",
        },
    },
    {
        "name": "L'Équipe",
        "url": "https://www.lequipe.fr/",
        "lang": "fr",
        "render_js": False,
        "selectors": {
            "articles": "article, .article",
            "title": "h2, h3",
            "link": "a",
            "date": "time",
        },
    },
    {
        "name": "Sky Sports",
        "url": "https://www.skysports.com/",
        "lang": "en",
        "render_js": True,  # Besoin de JS pour ce site
        "selectors": {
            "articles": "article, .news-list__item",
            "title": "h2, h3",
            "link": "a",
            "date": "time",
        },
    },
]


def scrape_with_requests_html(source: dict, retries: int = 2) -> list[dict]:
    """Scrape avec Requests-HTML (syntaxe simple)"""
    articles = []
    
    for attempt in range(retries):
        try:
            if attempt == 0:
                js_flag = " [JS]" if source["render_js"] else ""
                print(f"  🌐 {source['name']}{js_flag}…", end="", flush=True)
            else:
                print(f"  🔄 Retry {attempt}…", end="", flush=True)
            
            session = HTMLSession()
            session.headers.update(HEADERS)
            
            # Récupérer la page
            r = session.get(source["url"], timeout=15)
            
            # Optionnel: Rendre le JavaScript
            if source.get("render_js", False):
                r.html.render(timeout=10, sleep=1)
            
            today = datetime.now().strftime("%Y-%m-%d")
            found_titles = set()
            sel = source["selectors"]
            
            # ─── STRATÉGIE 1: Sélecteurs CSS ───
            containers = r.html.find(sel["articles"])
            for container in containers[:30]:
                try:
                    # Titre
                    title_elem = container.find(sel["title"], first=True)
                    title = title_elem.text.strip() if title_elem else ""
                    
                    if len(title) < 10 or title in found_titles:
                        continue
                    
                    # URL
                    link_elem = container.find("a", first=True)
                    url = ""
                    if link_elem:
                        href = link_elem.attrs.get("href", "").strip()
                        url = href if href.startswith("http") else source["url"].rstrip("/") + "/" + href.lstrip("/")
                    
                    # Date
                    date_elem = container.find("time", first=True)
                    date = today
                    if date_elem:
                        date = (date_elem.attrs.get("datetime", today))[:10]
                    
                    if title and url:
                        found_titles.add(title)
                        articles.append({
                            "title": title,
                            "source": source["name"],
                            "lang": source["lang"],
                            "url": url,
                            "date": date,
                            "summary": "",
                            "category": "",
                            "credibility": 0,
                        })
                except Exception:
                    pass
            
            # ─── STRATÉGIE 2: Tous les h1-h3 ───
            if len(articles) < 5:
                for tag in r.html.find("h1, h2, h3")[:40]:
                    try:
                        title = tag.text.strip()
                        if len(title) < 10 or title in found_titles:
                            continue
                        
                        link = tag.find("a", first=True)
                        if not link:
                            # Chercher le parent a
                            link = tag.element
                            while link:
                                if link.tag == "a":
                                    break
                                link = link.getparent()
                        
                        url = ""
                        if link is not None:
                            href = link.get("href", "").strip() if hasattr(link, 'get') else ""
                            if href:
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
            
            print(f" {len(articles)} articles")
            break
            
        except Exception as e:
            print(f" ❌", end="")
            if attempt < retries - 1:
                time.sleep(2)
    
    if not articles:
        print(f" ⚠️ Aucun article")
    
    return articles


def scrape_all_requests_html(output_path: str, delay: float = 2.0) -> pd.DataFrame:
    """Scrape avec Requests-HTML"""
    all_articles = []
    print(f"\n🌐 Requests-HTML Scraping ({len(SOURCES)} sources)\n")
    
    for i, source in enumerate(SOURCES, 1):
        print(f"[{i}/{len(SOURCES)}]", end=" ")
        articles = scrape_with_requests_html(source, retries=2)
        all_articles.extend(articles)
        
        if i < len(SOURCES):
            time.sleep(delay + random.uniform(0.5, 2.0))
    
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
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(BASE, "data", "output", "articles_rhtml.csv")
    scrape_all_requests_html(out)
