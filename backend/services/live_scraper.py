"""
live_scraper.py — MercatoPulse Lightweight Live Scraper
Scrapes 20 essential RSS sources, extracts entities via local NLP,
and inserts directly into the database. Designed to run in < 10 seconds.
"""

from __future__ import annotations

import hashlib
import logging
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# 20 Essential Sources — Fast, Reliable, Multilingual
# ─────────────────────────────────────────────────────────
LIVE_SOURCES = [
    # ── FR — Sources directes mercato ──
    {
        "name": "Foot Mercato",
        "url": "https://www.footmercato.net/feed",
        "lang": "fr",
        "category_default": "Ligue 1 🇫🇷",
    },
    {
        "name": "L'Équipe Mercato",
        "url": "https://www.lequipe.fr/rss/actu_rss_Football.xml",
        "lang": "fr",
        "category_default": "Ligue 1 🇫🇷",
    },
    {
        "name": "RMC Sport Mercato",
        "url": "https://rmcsport.bfmtv.com/rss/football/transferts/",
        "lang": "fr",
        "category_default": "Ligue 1 🇫🇷",
    },
    {
        "name": "Maxifoot Transferts",
        "url": "https://www.maxifoot.fr/rss/football.xml",
        "lang": "fr",
        "category_default": "Ligue 1 🇫🇷",
    },
    {
        "name": "Le10Sport",
        "url": "https://le10sport.com/feed",
        "lang": "fr",
        "category_default": "Ligue 1 🇫🇷",
    },
    # ── EN — Premier League & Global ──
    {
        "name": "Sky Sports Transfer Centre",
        "url": "https://www.skysports.com/rss/12040",
        "lang": "en",
        "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    },
    {
        "name": "BBC Sport Football",
        "url": "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "lang": "en",
        "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    },
    {
        "name": "CaughtOffside",
        "url": "https://www.caughtoffside.com/feed/",
        "lang": "en",
        "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    },
    {
        "name": "Football365",
        "url": "https://www.football365.com/feed",
        "lang": "en",
        "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    },
    {
        "name": "TeamTalk",
        "url": "https://www.teamtalk.com/feed",
        "lang": "en",
        "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    },
    {
        "name": "Football Insider",
        "url": "https://www.footballinsider247.com/feed/",
        "lang": "en",
        "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    },
    {
        "name": "The Athletic Football",
        "url": "https://theathletic.com/feed/rss/football/",
        "lang": "en",
        "category_default": "Champions League 🇪🇺",
    },
    # ── ES — La Liga ──
    {
        "name": "Marca Fútbol",
        "url": "https://e00-marca.uecdn.es/rss/futbol/futbol-internacional.xml",
        "lang": "es",
        "category_default": "La Liga 🇪🇸",
    },
    {
        "name": "AS Fichajes",
        "url": "https://feeds.feedburner.com/as/futbol",
        "lang": "es",
        "category_default": "La Liga 🇪🇸",
    },
    {
        "name": "Sport.es",
        "url": "https://www.sport.es/es/rss/futbol/index.xml",
        "lang": "es",
        "category_default": "La Liga 🇪🇸",
    },
    # ── IT — Serie A ──
    {
        "name": "Calciomercato.com",
        "url": "https://www.calciomercato.com/feed",
        "lang": "it",
        "category_default": "Serie A 🇮🇹",
    },
    {
        "name": "Tuttosport",
        "url": "https://www.tuttosport.com/rss/calcio.xml",
        "lang": "it",
        "category_default": "Serie A 🇮🇹",
    },
    # ── DE — Bundesliga ──
    {
        "name": "Kicker Transfers",
        "url": "https://rss.kicker.de/news/aktuell",
        "lang": "de",
        "category_default": "Bundesliga 🇩🇪",
    },
    # ── PT — Liga Portugal ──
    {
        "name": "A Bola",
        "url": "https://www.abola.pt/rss/index.aspx",
        "lang": "pt",
        "category_default": "Liga Portugal 🇵🇹",
    },
    # ── Global — Transfer specialists ──
    {
        "name": "Transfermarkt News",
        "url": "https://www.transfermarkt.com/rss/news",
        "lang": "en",
        "category_default": "Champions League 🇪🇺",
    },
    {
        "name": "90min Football",
        "url": "https://www.90min.com/posts.rss",
        "lang": "en",
        "category_default": "Champions League 🇪🇺",
    },
]

# ─────────────────────────────────────────────────────────
# League Classification Keywords
# ─────────────────────────────────────────────────────────
LEAGUE_KEYWORDS = {
    "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿": [
        "premier league", "manchester city", "man city", "arsenal", "liverpool",
        "manchester united", "man utd", "chelsea", "tottenham", "spurs",
        "newcastle", "aston villa", "west ham", "brighton", "everton",
    ],
    "La Liga 🇪🇸": [
        "la liga", "real madrid", "barcelona", "barça", "fc barcelone",
        "atletico", "atlético", "sevilla", "villarreal", "athletic bilbao",
        "real sociedad",
    ],
    "Ligue 1 🇫🇷": [
        "ligue 1", "psg", "paris saint-germain", "olympique de marseille",
        "om", "lyon", "monaco", "lille", "rennes", "nice", "lens",
        "marseille",
    ],
    "Serie A 🇮🇹": [
        "serie a", "inter milan", "inter", "ac milan", "juventus", "juve",
        "napoli", "roma", "lazio", "atalanta", "fiorentina",
    ],
    "Bundesliga 🇩🇪": [
        "bundesliga", "bayern munich", "bayern", "borussia dortmund",
        "dortmund", "bayer leverkusen", "leverkusen", "rb leipzig",
    ],
    "Saudi Pro League 🇸🇦": [
        "saudi", "al nassr", "al-nassr", "al hilal", "al-hilal",
        "al ittihad", "al-ittihad", "al ahli", "al-ahli",
    ],
    "Champions League 🇪🇺": [
        "champions league", "ligue des champions", "europa league",
    ],
}

# ── In-Memory Club Badges (0ms Instant Lookup) ──
CLUB_BADGES = {
    "Manchester City": "https://upload.wikimedia.org/wikipedia/en/thumb/e/eb/Manchester_City_FC_badge.svg/500px-Manchester_City_FC_badge.svg.png",
    "Barcelona": "https://upload.wikimedia.org/wikipedia/en/thumb/4/47/FC_Barcelona_%28crest%29.svg/500px-FC_Barcelona_%28crest%29.svg.png",
    "FC Barcelone": "https://upload.wikimedia.org/wikipedia/en/thumb/4/47/FC_Barcelona_%28crest%29.svg/500px-FC_Barcelona_%28crest%29.svg.png",
    "Real Madrid": "https://upload.wikimedia.org/wikipedia/en/thumb/5/56/Real_Madrid_CF.svg/500px-Real_Madrid_CF.svg.png",
    "Liverpool": "https://upload.wikimedia.org/wikipedia/en/thumb/0/0c/Liverpool_FC.svg/500px-Liverpool_FC.svg.png",
    "Arsenal": "https://upload.wikimedia.org/wikipedia/en/thumb/5/53/Arsenal_FC.svg/500px-Arsenal_FC.svg.png",
    "Chelsea": "https://upload.wikimedia.org/wikipedia/en/thumb/c/cc/Chelsea_FC.svg/500px-Chelsea_FC.svg.png",
    "Manchester United": "https://upload.wikimedia.org/wikipedia/en/thumb/7/7a/Manchester_United_FC_crest.svg/500px-Manchester_United_FC_crest.svg.png",
    "Paris Saint-Germain": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a7/Paris_Saint-Germain_F.C..svg/500px-Paris_Saint-Germain_F.C..svg.png",
    "PSG": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a7/Paris_Saint-Germain_F.C..svg/500px-Paris_Saint-Germain_F.C..svg.png",
    "Bayern Munich": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/FC_Bayern_M%C3%BCnchen_logo_%282017%29.svg/500px-FC_Bayern_M%C3%BCnchen_logo_%282017%29.svg.png",
    "Juventus": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/Juventus_FC_2017_icon_%28black%29.svg/500px-Juventus_FC_2017_icon_%28black%29.svg.png",
    "Inter Milan": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/FC_Internazionale_Milano_2021.svg/500px-FC_Internazionale_Milano_2021.svg.png",
    "AC Milan": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Logo_of_AC_Milan.svg/500px-Logo_of_AC_Milan.svg.png",
    "Atletico Madrid": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f4/Atletico_Madrid_2017_logo.svg/500px-Atletico_Madrid_2017_logo.svg.png",
    "Atlético de Madrid": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f4/Atletico_Madrid_2017_logo.svg/500px-Atletico_Madrid_2017_logo.svg.png",
    "Tottenham": "https://upload.wikimedia.org/wikipedia/en/thumb/b/b4/Tottenham_Hotspur.svg/500px-Tottenham_Hotspur.svg.png",
    "Newcastle": "https://upload.wikimedia.org/wikipedia/en/thumb/5/56/Newcastle_United_Logo.svg/500px-Newcastle_United_Logo.svg.png",
    "Aston Villa": "https://upload.wikimedia.org/wikipedia/en/thumb/9/9f/Aston_Villa_logo.svg/500px-Aston_Villa_logo.svg.png",
    "Sporting CP": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e1/Sporting_Clube_de_Portugal_%28Logo%29.svg/500px-Sporting_Clube_de_Portugal_%28Logo%29.svg.png",
    "Benfica": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a2/SL_Benfica_logo.svg/500px-SL_Benfica_logo.svg.png",
    "Porto": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f1/FC_Porto.svg/500px-FC_Porto.svg.png",
    "Al-Hilal": "https://upload.wikimedia.org/wikipedia/en/thumb/4/4b/Al_Hilal_SFC_Logo.svg/500px-Al_Hilal_SFC_Logo.svg.png",
    "Al-Nassr": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c5/Al_Nassr_FC_logo.svg/500px-Al_Nassr_FC_logo.svg.png",
    "Al-Ittihad": "https://upload.wikimedia.org/wikipedia/en/thumb/4/4e/Al-Ittihad_Club_%28Jeddah%29_logo.svg/500px-Al-Ittihad_Club_%28Jeddah%29_logo.svg.png",
    "Al-Ahli": "https://upload.wikimedia.org/wikipedia/en/thumb/b/b5/Al-Ahli_Saudi_FC_Logo.svg/500px-Al-Ahli_Saudi_FC_Logo.svg.png",
    "OM": "https://upload.wikimedia.org/wikipedia/fr/thumb/4/43/Logo_Olympique_de_Marseille.svg/500px-Logo_Olympique_de_Marseille.svg.png",
    "Lens": "https://upload.wikimedia.org/wikipedia/fr/thumb/7/74/Racing_Club_de_Lens_logo.svg/500px-Racing_Club_de_Lens_logo.svg.png",
    "RC Lens": "https://upload.wikimedia.org/wikipedia/fr/thumb/7/74/Racing_Club_de_Lens_logo.svg/500px-Racing_Club_de_Lens_logo.svg.png",
    "Nice": "https://upload.wikimedia.org/wikipedia/fr/thumb/b/b1/Logo_OGC_Nice_2013.svg/500px-Logo_OGC_Nice_2013.svg.png",
    "OGC Nice": "https://upload.wikimedia.org/wikipedia/fr/thumb/b/b1/Logo_OGC_Nice_2013.svg/500px-Logo_OGC_Nice_2013.svg.png",
    "Rennes": "https://upload.wikimedia.org/wikipedia/fr/thumb/e/e9/Logo_Stade_Rennais_FC.svg/500px-Logo_Stade_Rennais_FC.svg.png",
    "Stade Rennais": "https://upload.wikimedia.org/wikipedia/fr/thumb/e/e9/Logo_Stade_Rennais_FC.svg/500px-Logo_Stade_Rennais_FC.svg.png",
    "Monaco": "https://upload.wikimedia.org/wikipedia/fr/thumb/b/ba/AS_Monaco_FC_%28logo%29.svg/500px-AS_Monaco_FC_%28logo%29.svg.png",
    "AS Monaco": "https://upload.wikimedia.org/wikipedia/fr/thumb/b/ba/AS_Monaco_FC_%28logo%29.svg/500px-AS_Monaco_FC_%28logo%29.svg.png",
    "Lyon": "https://upload.wikimedia.org/wikipedia/fr/thumb/e/e2/Olympique_lyonnais_%28logo%29.svg/500px-Olympique_lyonnais_%28logo%29.svg.png",
    "OL": "https://upload.wikimedia.org/wikipedia/fr/thumb/e/e2/Olympique_lyonnais_%28logo%29.svg/500px-Olympique_lyonnais_%28logo%29.svg.png",
}

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Safari/537.36"
)


def _clean_html(text: str) -> str:
    """Strip HTML tags from text."""
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()


def _classify_league(title: str, summary: str, default: str) -> str:
    """Classify article into a league based on keywords."""
    text = f"{title} {summary}".lower()
    for league, keywords in LEAGUE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return league
    return default


def _detect_status(title: str) -> str:
    """Detect transfer status from title."""
    t = title.lower()
    if any(k in t for k in ["officiel", "official", "signe", "signé", "prolonge", "confirmé", "signs for", "joins"]):
        return "OFFICIEL ✅"
    if any(k in t for k in ["here we go", "accord total", "deal done", "visite médicale", "agree"]):
        return "HERE WE GO 🔥"
    if any(k in t for k in ["négociation", "pourparlers", "offre", "discussions", "proche", "talks", "bid", "close to"]):
        return "NEGOCIATION 💬"
    return "RUMEUR 📰"


def _extract_fee(title: str, summary: str) -> tuple[str, float]:
    """Extract transfer fee from text."""
    text = f"{title} {summary}"
    # Match patterns like 85M€, €85m, 85 million, £8.6m
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*[Mm](?:illion)?[s]?\s*[€£$]|[€£$]\s*(\d+(?:[.,]\d+)?)\s*[Mm]|(\d+(?:[.,]\d+)?)\s*M€', text)
    if m:
        val_str = m.group(1) or m.group(2) or m.group(3)
        try:
            val = float(val_str.replace(",", "."))
            return f"{val:.0f}M€", val
        except (ValueError, TypeError):
            pass
    # Match "X million"
    m2 = re.search(r'(\d+(?:[.,]\d+)?)\s*million', text, re.IGNORECASE)
    if m2:
        try:
            val = float(m2.group(1).replace(",", "."))
            return f"{val:.0f}M€", val
        except (ValueError, TypeError):
            pass
    return "Non communiqué", 0.0


def _build_external_key(source: str, title: str, url: str) -> str:
    """Build a dedup key for the article."""
    payload = f"{source}|{title}|{url}"
    return hashlib.sha1(payload.encode("utf-8", errors="ignore")).hexdigest()


def _fetch_rss_source(source: dict) -> list[dict]:
    """Fetch and parse a single RSS source. Returns list of article dicts."""
    url = source["url"]
    name = source["name"]
    lang = source.get("lang", "fr")
    cat_default = source.get("category_default", "Champions League 🇪🇺")

    articles = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read()

        root = ET.fromstring(data)
        for item in root.findall(".//item")[:30]:
            title_el = item.find("title")
            link_el = item.find("link")
            desc_el = item.find("description")
            pub_el = item.find("pubDate")

            title = _clean_html(title_el.text) if title_el is not None and title_el.text else ""
            link = link_el.text.strip() if link_el is not None and link_el.text else ""
            raw_desc = desc_el.text if desc_el is not None and desc_el.text else ""
            pub_date = pub_el.text.strip() if pub_el is not None and pub_el.text else ""

            if not title or not link:
                continue

            # Extract image from RSS item
            img_url = ""
            enc = item.find("enclosure")
            if enc is not None and enc.get("url"):
                img_url = enc.get("url", "")
            if not img_url:
                for child in item:
                    tag = child.tag.lower()
                    if "content" in tag or "thumbnail" in tag:
                        u = child.get("url", "")
                        if u and u.startswith("http"):
                            img_url = u
                            break
            if not img_url and raw_desc:
                img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', raw_desc)
                if img_match:
                    img_url = img_match.group(1)

            summary = _clean_html(raw_desc)[:400] if raw_desc else title

            articles.append({
                "title": title,
                "url": link,
                "raw_date": pub_date,
                "language": lang,
                "summary": summary,
                "image_url": img_url if img_url.startswith("http") else "",
                "category_default": cat_default,
                "source_name": name,
            })
    except Exception as e:
        logger.warning("Live scrape %s failed: %s", name, e)

    return articles


def _parse_rss_date(raw_date: str) -> Optional[datetime]:
    """Parse RSS date string into datetime."""
    if not raw_date:
        return None
    # Try RFC 2822 format (RSS standard)
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(raw_date.strip(), fmt)
        except ValueError:
            continue
    # Try partial parse
    try:
        # Handle "Mon, 30 Aug 2026 19:32:08 GMT"
        clean = raw_date.replace("GMT", "+0000").replace("UTC", "+0000")
        return datetime.strptime(clean.strip(), "%a, %d %b %Y %H:%M:%S %z")
    except ValueError:
        pass
    return None


def run_live_scrape(db: Session) -> dict:
    """
    Execute a lightweight live scrape of 20 essential sources,
    extract entities via local NLP, and insert directly into the database.

    Returns a summary dict with counts.
    """
    from backend.models import Article, Source

    logger.info("🚀 Live scrape: fetching %d sources in parallel...", len(LIVE_SOURCES))

    # 1. Fetch all sources in parallel
    all_raw = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_map = {executor.submit(_fetch_rss_source, src): src for src in LIVE_SOURCES}
        try:
            for future in as_completed(future_map, timeout=25):
                src = future_map[future]
                try:
                    result = future.result(timeout=5)
                    all_raw.extend(result)
                    if result:
                        logger.info("  ✅ %s → %d articles", src["name"], len(result))
                except Exception as e:
                    logger.warning("  ❌ %s → %s", src["name"], e)
        except TimeoutError:
            logger.warning("⚠️ Some sources timed out, continuing with %d articles collected so far", len(all_raw))

    logger.info("📊 Total raw articles fetched: %d", len(all_raw))

    if not all_raw:
        return {"status": "ok", "fetched": 0, "new_inserted": 0, "total_in_db": 0}

    # 2. Deduplicate by title (normalized)
    seen = set()
    unique_articles = []
    for art in all_raw:
        key = re.sub(r"\W+", "", art["title"].lower())[:60]
        if key not in seen:
            seen.add(key)
            unique_articles.append(art)
    logger.info("📊 After dedup: %d unique articles", len(unique_articles))

    # 3. Load NLP extractor
    try:
        from src.mercato_nlp import parse_article_full, is_football_mercato_article
        has_nlp = True
    except ImportError:
        try:
            from mercato_nlp import parse_article_full, is_football_mercato_article
            has_nlp = True
        except ImportError:
            has_nlp = False
            logger.warning("NLP module not available, using basic extraction")

    # 4. Get existing external keys to avoid duplicates
    existing_keys = {
        row[0] for row in db.query(Article.external_key).all() if row[0]
    }

    # 5. Ensure sources exist
    existing_sources = {s.name: s for s in db.query(Source).all()}
    now = datetime.utcnow()

    # 6. Process each article
    to_insert = []
    skipped_nlp = 0
    skipped_dup = 0

    for art in unique_articles:
        title = art["title"]
        summary = art["summary"]
        source_name = art["source_name"]

        # Football filter
        if has_nlp:
            if not is_football_mercato_article(title, summary, source=source_name):
                skipped_nlp += 1
                continue

        # Build external key
        ext_key = _build_external_key(source_name, title, art["url"])
        if ext_key in existing_keys:
            skipped_dup += 1
            continue

        # Ensure source exists
        if source_name not in existing_sources:
            src_obj = Source(
                name=source_name,
                credibility_score=4.0,
                active=True,
                created_at=now,
                updated_at=now,
            )
            db.add(src_obj)
            db.flush()
            existing_sources[source_name] = src_obj

        source_id = existing_sources[source_name].id

        # NLP extraction
        if has_nlp:
            entities = parse_article_full(title, summary)
            player_name = entities.get("player_name", "")
            from_club = entities.get("from_club", "")
            to_club = entities.get("to_club", "")
            status = entities.get("status", _detect_status(title))
            national_team = entities.get("national_team", "")
        else:
            player_name = ""
            from_club = ""
            to_club = ""
            status = _detect_status(title)
            national_team = ""

        # League classification
        league = _classify_league(title, summary, art["category_default"])

        # Fee extraction
        fee_str, fee_num = _extract_fee(title, summary)

        # Sentiment
        if "OFFICIEL" in status or "HERE WE GO" in status:
            sentiment = "Positif"
        else:
            sentiment = "Neutre"

        # Published date
        published_at = _parse_rss_date(art["raw_date"]) or now

        # Image URL (RSS first, then in-memory club badge fallback, 0ms)
        img_url = art.get("image_url") or None
        if not img_url or not img_url.startswith("http"):
            if to_club and to_club in CLUB_BADGES:
                img_url = CLUB_BADGES[to_club]
            elif from_club and from_club in CLUB_BADGES:
                img_url = CLUB_BADGES[from_club]
            else:
                img_url = None
        if img_url and not img_url.startswith("http"):
            img_url = None

        # Semantic hash for further dedup
        sem_parts = [
            re.sub(r"\W+", "_", (player_name or "").lower()),
            re.sub(r"\W+", "_", (from_club or "").lower()),
            re.sub(r"\W+", "_", (to_club or "").lower()),
        ]
        semantic_hash = "__".join(p for p in sem_parts if p)

        to_insert.append({
            "external_key": ext_key,
            "title": title,
            "url": art["url"],
            "raw_date": art["raw_date"][:128] if art["raw_date"] else None,
            "published_at": published_at,
            "language": art["language"],
            "category": league,
            "sentiment": sentiment,
            "player_name": player_name or None,
            "from_club": from_club or None,
            "to_club": to_club or None,
            "league": league,
            "transfer_fee": fee_str,
            "status": status,
            "summary": summary,
            "image_url": img_url,
            "image_caption": None,
            "credibility_score": 4.0,
            "fee_numeric": fee_num,
            "semantic_hash": semantic_hash or None,
            "source_id": source_id,
            "created_at": now,
            "updated_at": now,
        })
        existing_keys.add(ext_key)

    # 7. Bulk insert with ON CONFLICT DO NOTHING (handles race conditions with scheduler)
    new_count = 0
    if to_insert:
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from sqlalchemy import inspect as sa_inspect
        chunk_size = 200
        for i in range(0, len(to_insert), chunk_size):
            chunk = to_insert[i:i + chunk_size]
            try:
                stmt = pg_insert(Article.__table__).values(chunk)
                stmt = stmt.on_conflict_do_nothing(index_elements=["external_key"])
                result = db.execute(stmt)
                new_count += result.rowcount
            except Exception as e:
                logger.warning("Chunk insert error (falling back to individual): %s", e)
                db.rollback()
                # Fallback: insert one-by-one, skip duplicates
                for row in chunk:
                    try:
                        stmt = pg_insert(Article.__table__).values(row)
                        stmt = stmt.on_conflict_do_nothing(index_elements=["external_key"])
                        result = db.execute(stmt)
                        new_count += result.rowcount
                    except Exception:
                        db.rollback()
        db.commit()

    # 8. Auto-purge articles older than 90 days
    purged = 0
    try:
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=90)
        purged = db.query(Article).filter(Article.published_at < cutoff).delete()
        if purged > 0:
            db.commit()
            logger.info("🗑️ Purged %d old articles (>90 days)", purged)
    except Exception as e:
        logger.warning("Purge error: %s", e)

    total = db.query(Article).count()

    logger.info(
        "✅ Live scrape complete: %d new inserted, %d skipped (dup), %d filtered (NLP), %d purged old, %d total in DB",
        new_count, skipped_dup, skipped_nlp, purged, total,
    )

    return {
        "status": "ok",
        "fetched": len(all_raw),
        "unique": len(unique_articles),
        "new_inserted": new_count,
        "skipped_duplicate": skipped_dup,
        "skipped_not_football": skipped_nlp,
        "purged_old": purged,
        "total_in_db": total,
    }
