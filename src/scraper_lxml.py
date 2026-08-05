#!/usr/bin/env python3
"""
scraper_lxml.py — Scraping avec LXML (ultra-rapide)
Alternative à BeautifulSoup pour la performance
"""

import requests
from lxml import html
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
    "Accept-Language": "ar-SA,ar;q=0.9,fr-FR;q=0.8,fr;q=0.7,en;q=0.6",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

SOURCES = [
    {
        "name": "BBC Sport",
        "url": "https://www.bbc.com/sport",
        "lang": "en",
        "xpaths": {
            "articles": "//article | //div[@class='gs-c-promo']",
            "title": ".//h3//text() | .//h2//text() | .//span[@class='gs-c-promo-heading__title']//text()",
            "link": ".//a/@href",
            "date": ".//time/@datetime",
        },
    },
    {
        "name": "L'Équipe",
        "url": "https://www.lequipe.fr/",
        "lang": "fr",
        "xpaths": {
            "articles": "//article | //div[@class='article']",
            "title": ".//h2//text() | .//h3//text() | .//span[@class='article__title']//text()",
            "link": ".//a/@href",
            "date": ".//time/@datetime",
        },
    },
    {
        "name": "Goal.com",
        "url": "https://www.goal.com/en",
        "lang": "en",
        "xpaths": {
            "articles": "//article | //div[@class='js-article']",
            "title": ".//h3//text() | .//h2//text() | .//span//text()",
            "link": ".//a/@href",
            "date": ".//time/@datetime",
        },
    },
]


def scrape_with_lxml(source: dict, retries: int = 3) -> list[dict]:
    """Scrape avec LXML (XPath) - Plus rapide que BeautifulSoup"""
    articles = []
    
    for attempt in range(retries):
        try:
            if attempt == 0:
                print(f"  🌐 {source['name']}…", end="", flush=True)
            else:
                print(f"  🔄 Retry {attempt}…", end="", flush=True)
            
            session = requests.Session()
            session.headers.update(HEADERS)
            resp = session.get(source["url"], timeout=15)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            
            # Parsing avec LXML
            tree = html.fromstring(resp.text)
            
            today = datetime.now().strftime("%Y-%m-%d")
            found_titles = set()
            
            # ─── STRATÉGIE 1: XPath selectors ───
            containers = tree.xpath(source["xpaths"]["articles"])
            for container in containers[:30]:
                try:
                    # Extraire titre
                    titles = container.xpath(source["xpaths"]["title"])
                    if not titles:
                        continue
                    title = titles[0].strip() if titles[0] else ""
                    
                    if len(title) < 10 or title in found_titles:
                        continue
                    
                    # Extraire URL
                    links = container.xpath(source["xpaths"]["link"])
                    url = ""
                    if links:
                        href = links[0].strip()
                        url = href if href.startswith("http") else source["url"].rstrip("/") + "/" + href.lstrip("/")
                    
                    # Extraire date
                    dates = container.xpath(source["xpaths"]["date"])
                    date = dates[0][:10] if dates else today
                    
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
            
            # ─── STRATÉGIE 2: Tous les h1-h3 si peu de résultats ───
            if len(articles) < 5:
                for tag in tree.xpath("//h1 | //h2 | //h3")[:40]:
                    try:
                        title = "".join(tag.xpath(".//text()")).strip()
                        if len(title) < 10 or title in found_titles:
                            continue
                        
                        # Chercher lien parent
                        link_elem = tag.xpath(".//ancestor::a/@href | .//@href")
                        url = ""
                        if link_elem:
                            href = link_elem[0].strip()
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


def scrape_all_lxml(output_path: str, delay: float = 2.0) -> pd.DataFrame:
    """Scrape toutes les sources avec LXML"""
    all_articles = []
    print(f"\n⚡ LXML Scraping ({len(SOURCES)} sources)\n")
    
    for i, source in enumerate(SOURCES, 1):
        print(f"[{i}/{len(SOURCES)}]", end=" ")
        articles = scrape_with_lxml(source, retries=2)
        all_articles.extend(articles)
        
        if i < len(SOURCES):
            time.sleep(delay + random.uniform(0.5, 2.0))
    
    df = pd.DataFrame(all_articles)
    if df.empty:
        print("\n⚠️ Aucun article collecté")
        return df
    
    before = len(df)
    df = df.drop_duplicates(subset=["title"])
    after = len(df)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    print(f"\n✅ {after} articles → {output_path}")
    print(f"📊 Par source:")
    for src, n in df["source"].value_counts().items():
        print(f"   {src:20s}: {n}")
    
    return df


if __name__ == "__main__":
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(BASE, "data", "output", "articles_lxml.csv")
    scrape_all_lxml(out)
