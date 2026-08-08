"""
data_enricher.py - Enrichissement des articles.
- Resumes automatiques
- Images prioritairement extraites des pages source
- Fallback Wikipedia avec verification de pertinence
"""

from __future__ import annotations

import os
import re
import time
from functools import lru_cache
from urllib.parse import quote, urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SportPulse-Enricher/1.0)",
    "Accept-Language": "fr-FR,fr;q=0.9,ar;q=0.8,en;q=0.7",
}

WIKIPEDIA_LANGS = ["ar", "fr", "en"]
STOPWORDS = {
    "a", "about", "actuellement", "actualites", "afrique", "al", "and", "articles", "avec", "aux",
    "be", "but", "can", "champions", "club", "coupe", "de", "des", "du", "en", "et", "europe",
    "football", "fr", "il", "in", "la", "le", "les", "ligue", "live", "monde", "news", "of", "on",
    "ou", "par", "pour", "pro", "sport", "sports", "sur", "the", "to", "uefa", "un", "une", "video",
}


def clean_text(text: str) -> str:
    if not text:
        return ""
    value = str(text)
    value = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", value)
    value = re.sub(r"\s+", " ", value)
    value = value.replace("&nbsp;", " ").replace("&amp;", "&")
    value = value.replace("&lt;", "<").replace("&gt;", ">")
    return value.strip()


def tokenize(text: str) -> set[str]:
    cleaned = clean_text(text).lower()
    tokens = re.findall(r"[a-z0-9\u00c0-\u024f\u0600-\u06ff]{3,}", cleaned)
    return {token for token in tokens if token not in STOPWORDS}


def looks_like_wikipedia_match(title: str, candidate_title: str) -> bool:
    title_tokens = tokenize(title)
    candidate_tokens = tokenize(candidate_title)
    if not title_tokens or not candidate_tokens:
        return False

    overlap = title_tokens & candidate_tokens
    if len(title_tokens) <= 2:
        return len(overlap) == len(title_tokens)
    if len(title_tokens) <= 4:
        return len(overlap) >= 2
    return len(overlap) >= max(2, len(title_tokens) // 3)


def is_remote_image(url: str) -> bool:
    value = clean_text(url)
    return value.startswith(("http://", "https://"))


def is_wikipedia_image(url: str) -> bool:
    host = urlparse(clean_text(url)).netloc.lower()
    return host.endswith("wikipedia.org") or host.endswith("wikimedia.org")


def is_article_like_url(url: str) -> bool:
    path = urlparse(clean_text(url)).path.strip("/")
    if not path:
        return False

    segments = [segment for segment in path.split("/") if segment]
    if len(segments) >= 3:
        return True

    slug = segments[-1]
    if slug.count("-") >= 4:
        return True
    return bool(re.search(r"[A-Z0-9]{6,}", slug))


def detect_article_lang(title: str) -> str:
    arabic = len(re.findall(r"[\u0600-\u06FF]", title))
    total = len(title.replace(" ", ""))
    if total == 0:
        return "fr"
    if arabic / total > 0.25:
        return "ar"
    fr_words = ["le", "la", "les", "du", "des", "un", "une", "et", "en", "au", "aux"]
    words = title.lower().split()
    if any(word in fr_words for word in words[:5]):
        return "fr"
    return "en"


def extract_first_paragraph(soup: BeautifulSoup, max_chars: int = 300) -> str:
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    for paragraph in soup.find_all("p"):
        text = clean_text(paragraph.get_text())
        if len(text) > 60:
            return text[:max_chars] + ("..." if len(text) > max_chars else "")
    return ""


@lru_cache(maxsize=512)
def fetch_article_metadata(url: str) -> dict:
    if not url or not url.startswith("http"):
        return {}

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        def get_meta(*selectors: tuple[str, str]) -> str:
            for attr, value in selectors:
                node = soup.find("meta", attrs={attr: value})
                content = clean_text(node.get("content", "")) if node else ""
                if content:
                    return content
            return ""

        summary = get_meta(
            ("property", "og:description"),
            ("name", "description"),
            ("name", "twitter:description"),
        )
        if not summary:
            summary = extract_first_paragraph(soup)

        image_url = get_meta(
            ("property", "og:image"),
            ("name", "twitter:image"),
            ("property", "twitter:image"),
        )
        if image_url:
            image_url = urljoin(url, image_url)

        image_caption = get_meta(
            ("property", "og:image:alt"),
            ("name", "twitter:image:alt"),
        )
        if not image_caption:
            image_caption = summary

        return {
            "summary": clean_text(summary),
            "image_url": clean_text(image_url),
            "image_caption": clean_text(image_caption),
        }
    except Exception:
        return {}


def extract_summary_from_url(url: str, max_chars: int = 300) -> str:
    summary = clean_text(fetch_article_metadata(url).get("summary", ""))
    if not summary:
        return ""
    return summary[:max_chars] + ("..." if len(summary) > max_chars else "")


def fetch_wikipedia_image(title: str, lang: str = "fr") -> dict:
    for wiki_lang in ([lang] + [value for value in WIKIPEDIA_LANGS if value != lang]):
        try:
            search_url = f"https://{wiki_lang}.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": title,
                "srlimit": 1,
            }
            response = requests.get(search_url, params=params, headers=HEADERS, timeout=8)
            data = response.json()
            results = data.get("query", {}).get("search", [])
            if not results:
                continue

            page_title = results[0]["title"]
            if not looks_like_wikipedia_match(title, page_title):
                continue

            rest_url = f"https://{wiki_lang}.wikipedia.org/api/rest_v1/page/summary/{quote(page_title)}"
            page_response = requests.get(rest_url, headers=HEADERS, timeout=8)
            if not page_response.ok:
                continue
            page = page_response.json()

            thumbnail = page.get("thumbnail", {})
            if thumbnail.get("source"):
                image_url = re.sub(r"/\d+px-", "/800px-", thumbnail["source"])
                return {
                    "url": clean_text(image_url),
                    "caption": clean_text(page.get("description", "")),
                    "source": f"Wikipedia ({wiki_lang})",
                }
        except Exception:
            continue
    return {}


def ensure_canonical_columns(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    frame.columns = [str(col).strip().lower() for col in frame.columns]

    if "summary" not in frame.columns:
        frame["summary"] = frame["resume"] if "resume" in frame.columns else ""
    elif "resume" in frame.columns:
        current = frame["summary"].fillna("").astype(str)
        resume_values = frame["resume"].fillna("").astype(str)
        frame.loc[current.isin(["", "nan"]), "summary"] = resume_values

    if "image_url" not in frame.columns:
        frame["image_url"] = ""
    if "image_caption" not in frame.columns:
        frame["image_caption"] = ""
    if "lang" not in frame.columns:
        frame["lang"] = frame["title"].apply(detect_article_lang) if "title" in frame.columns else "fr"

    for column in ["summary", "image_url", "image_caption", "lang", "title", "url"]:
        if column in frame.columns:
            frame[column] = frame[column].fillna("").astype("object")

    return frame


def enrich_dataframe(
    df: pd.DataFrame,
    enrich_images: bool = True,
    enrich_summaries: bool = True,
    max_articles: int | None = None,
) -> pd.DataFrame:
    if df.empty:
        return df

    frame = ensure_canonical_columns(df)
    limit = min(max_articles or len(frame), len(frame))
    print(f"\nEnrichissement de {limit} articles...")

    for index, row_index in enumerate(frame.index[:limit]):
        row = frame.loc[row_index]
        title = str(row.get("title", ""))
        url = str(row.get("url", ""))
        lang = str(row.get("lang", "fr"))

        print(f"  [{index + 1:3d}/{limit}] {title[:55]}...", end="\r")

        current_summary = str(row.get("summary", "")).strip()
        current_image = str(row.get("image_url", "")).strip()
        article_like_url = is_article_like_url(url)
        needs_summary = enrich_summaries and (not current_summary or current_summary == "nan")
        needs_better_image = enrich_images and (
            not current_image
            or current_image == "nan"
            or is_wikipedia_image(current_image)
        )
        page_data = fetch_article_metadata(url) if article_like_url and (needs_summary or needs_better_image) else {}

        if needs_summary:
            summary = clean_text(page_data.get("summary", "")) or extract_summary_from_url(url)
            if summary:
                frame.at[row_index, "summary"] = summary

        if needs_better_image:
            try:
                from src.photo_enricher import resolve_photo_for_article
                best_img = resolve_photo_for_article(
                    article_url=url,
                    player_name=str(row.get("player_name", "")),
                    to_club=str(row.get("to_club", "")),
                    from_club=str(row.get("from_club", "")),
                    current_image=current_image,
                )
                if best_img:
                    frame.at[row_index, "image_url"] = best_img
            except Exception:
                source_image = clean_text(page_data.get("image_url", ""))
                if is_remote_image(source_image):
                    frame.at[row_index, "image_url"] = source_image

        time.sleep(0.3)

    print("\nEnrichissement termine")
    return frame


def run_enrichment(
    input_path: str,
    output_path: str,
    images: bool = True,
    summaries: bool = True,
    max_articles: int | None = None,
):
    print(f"Lecture : {input_path}")
    df = pd.read_csv(input_path, encoding="utf-8-sig")
    print(f"   {len(df)} articles charges")

    df = enrich_dataframe(
        df,
        enrich_images=images,
        enrich_summaries=summaries,
        max_articles=max_articles,
    )

    ordered_columns = [
        column
        for column in ["title", "source", "lang", "url", "date", "summary", "category", "credibility", "image_url", "image_caption"]
        if column in df.columns
    ]
    remaining_columns = [column for column in df.columns if column not in ordered_columns and column != "resume"]
    df = df[ordered_columns + remaining_columns]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\nSauvegarde : {output_path}")

    image_count = (df["image_url"].notna() & (df["image_url"] != "")).sum()
    summary_count = (df["summary"].notna() & (df["summary"] != "")).sum()
    print(f"   Articles avec image  : {image_count}/{len(df)}")
    print(f"   Articles avec resume : {summary_count}/{len(df)}")

    return df


if __name__ == "__main__":
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(BASE, "data", "output", "organized_articles.csv")
    output_file = os.path.join(BASE, "data", "output", "organized_articles.csv")

    if not os.path.exists(input_file):
        print(f"Fichier introuvable : {input_file}")
    else:
        run_enrichment(input_file, output_file, images=True, summaries=True, max_articles=None)
