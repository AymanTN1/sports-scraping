"""
scraper.py — MarketPulse Multi-Source Financial & Market Scraper
Sources : Active verified financial & market news sources (FR / EN / AR).
"""

from __future__ import annotations

import os
import random
import time
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7,ar;q=0.6",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

# ─────────────────────────────────────────────
# SOURCES FINANCIÈRES VÉRIFIÉES & ACTIVES (FR / EN / AR)
# ─────────────────────────────────────────────
SOURCES = [
    # ── BOURSE & MARCHAIS MONDIAUX ──
    {
        "name": "Yahoo Finance",
        "url": "https://finance.yahoo.com/news/rssindex",
        "lang": "en",
        "category_default": "Bourse & Actions",
    },
    {
        "name": "CNBC Markets",
        "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "lang": "en",
        "category_default": "Bourse & Actions",
    },
    {
        "name": "MarketWatch",
        "url": "http://feeds.marketwatch.com/marketwatch/topstories/",
        "lang": "en",
        "category_default": "Bourse & Actions",
    },
    {
        "name": "WSJ Business",
        "url": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
        "lang": "en",
        "category_default": "Bourse & Actions",
    },
    {
        "name": "Seeking Alpha",
        "url": "https://seekingalpha.com/feed.xml",
        "lang": "en",
        "category_default": "Bourse & Actions",
    },
    {
        "name": "Investing.com",
        "url": "https://fr.investing.com/rss/news.rss",
        "lang": "fr",
        "category_default": "Bourse & Actions",
    },

    # ── MACROÉCONOMIE & BANQUES CENTRALES ──
    {
        "name": "Le Figaro Économie",
        "url": "https://www.lefigaro.fr/rss/figaro_economie.xml",
        "lang": "fr",
        "category_default": "Macroéconomie",
    },
    {
        "name": "Le Monde Économie",
        "url": "https://www.lemonde.fr/economie/rss_full.xml",
        "lang": "fr",
        "category_default": "Macroéconomie",
    },
    {
        "name": "Business Insider",
        "url": "https://www.businessinsider.com/rss",
        "lang": "en",
        "category_default": "Macroéconomie",
    },

    # ── CRYPTOMONNAIES & BLOCKCHAIN ──
    {
        "name": "CoinDesk",
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "lang": "en",
        "category_default": "Cryptomonnaies",
    },
    {
        "name": "CoinTelegraph",
        "url": "https://cointelegraph.com/rss",
        "lang": "en",
        "category_default": "Cryptomonnaies",
    },
    {
        "name": "Cryptoast",
        "url": "https://cryptoast.fr/feed/",
        "lang": "fr",
        "category_default": "Cryptomonnaies",
    },

    # ── ÉCONOMIE RÉGIONALE & ARABE (MENA) ──
    {
        "name": "Hespress Économie",
        "url": "https://www.hespress.com/economie/feed",
        "lang": "ar",
        "category_default": "Macroéconomie",
    },

    # ── FINTECH & STARTUPS ──
    {
        "name": "TechCrunch VC",
        "url": "https://techcrunch.com/category/venture/feed/",
        "lang": "en",
        "category_default": "Startups & VC",
    },
    {
        "name": "Maddyness",
        "url": "https://www.maddyness.com/feed/",
        "lang": "fr",
        "category_default": "Startups & VC",
    },
]


def clean_html(text: str) -> str:
    """Nettoie le texte des balises HTML et espaces superflus."""
    if not text:
        return ""
    text = BeautifulSoup(text, "html.parser").get_text()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_image_url(item) -> str:
    """Extrait l'URL de l'image principale depuis un élément RSS."""
    enclosure = item.find("enclosure")
    if enclosure is not None and enclosure.get("url"):
        return enclosure.get("url")

    for media in item.findall("{http://search.yahoo.com/mrss/}content"):
        if media.get("url"):
            return media.get("url")

    desc = item.find("description")
    if desc is not None and desc.text:
        soup = BeautifulSoup(desc.text, "html.parser")
        img = soup.find("img")
        if img and img.get("src"):
            return img.get("src")

    return ""


def parse_rss_feed(source: dict, retries: int = 2) -> list[dict]:
    """Scrape et parse un flux RSS financier."""
    name = source["name"]
    url = source["url"]
    lang = source["lang"]
    cat_default = source.get("category_default", "Macroéconomie")

    articles = []
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                time.sleep(1)
                continue

            content = resp.content
            root = ET.fromstring(content)
            items = root.findall(".//item")
            if not items:
                items = root.findall("{http://www.w3.org/2005/Atom}entry")

            for item in items[:25]:
                title_elem = item.find("title")
                if title_elem is None:
                    title_elem = item.find("{http://www.w3.org/2005/Atom}title")
                title = clean_html(title_elem.text) if title_elem is not None else ""

                if not title or len(title) < 10:
                    continue

                link_elem = item.find("link")
                if link_elem is None:
                    link_elem = item.find("{http://www.w3.org/2005/Atom}link")
                if link_elem is not None:
                    link = link_elem.text if link_elem.text else link_elem.get("href", "")
                else:
                    link = ""

                summary_elem = item.find("description")
                if summary_elem is None:
                    summary_elem = item.find("{http://www.w3.org/2005/Atom}summary")
                summary = clean_html(summary_elem.text) if summary_elem is not None else ""

                date_elem = item.find("pubDate")
                if date_elem is None:
                    date_elem = item.find("{http://www.w3.org/2005/Atom}updated")
                date_str = date_elem.text.strip() if date_elem is not None and date_elem.text else datetime.now().strftime("%Y-%m-%d")

                img_url = extract_image_url(item)

                articles.append({
                    "title": title,
                    "source": name,
                    "lang": lang,
                    "url": link,
                    "date": date_str,
                    "summary": summary[:300] if summary else title,
                    "category": cat_default,
                    "credibility": 4,
                    "image_url": img_url,
                    "image_caption": title,
                })

            if articles:
                print(f"  🌐 {name:22s}… ✅ {len(articles)} articles financiers")
                return articles

        except Exception as exc:
            time.sleep(1)

    print(f"  🌐 {name:22s}… ⚠️ Aucun article trouvé")
    return articles


def scrape_source(source: dict, retries: int = 2) -> list[dict]:
    """Scrape une source financière."""
    return parse_rss_feed(source, retries=retries)


def scrape_all(output_path: str = None, delay: float = 0.2) -> pd.DataFrame:
    """Scrape les sources financières actives et exporte en CSV."""
    all_articles = []
    print("\n" + "=" * 80)
    print(f"⚡ MARKETPULSE — SCRAPING MASSIF MULTI-SOURCES FINANCIÈRES ({len(SOURCES)} SOURCES)")
    print("=" * 80)

    for i, source in enumerate(SOURCES, 1):
        arts = scrape_source(source)
        all_articles.extend(arts)
        time.sleep(random.uniform(0.1, delay))

    df = pd.DataFrame(all_articles)
    if df.empty:
        df = pd.DataFrame(columns=[
            "title", "source", "lang", "url", "date", "summary", "category", "credibility", "image_url", "image_caption"
        ])

    if not df.empty and "title" in df.columns:
        df = df.drop_duplicates(subset=["title"]).reset_index(drop=True)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n✅ {len(df)} articles financiers sauvegardés dans : {output_path}")

    return df


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(base_dir, "data", "output", "articles_test.csv")
    scrape_all(out, delay=0.2)
