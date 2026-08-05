from __future__ import annotations

import html
import re
import shutil
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "output"
DOCS_DIR = BASE_DIR / "docs"
REPORTS_DIR = DOCS_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def clean_value(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in {"", "nan", "nat", "none", "null"}:
        return ""
    return text


def polish_text(value) -> str:
    text = clean_value(value)
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"([,;:!?])([^\s])", r"\1 \2", text)
    text = re.sub(r"([a-zà-öø-ÿ])([A-ZÀ-ÖØ-Þ])", r"\1 \2", text)
    text = re.sub(r"([0-9])([A-Za-zÀ-ÿ])", r"\1 \2", text)
    text = re.sub(r"([A-Za-zÀ-ÿ])([0-9])", r"\1 \2", text)
    return text.strip()


def find_columns(df: pd.DataFrame, *aliases: str) -> list[str]:
    aliases = tuple(alias.lower() for alias in aliases)
    matches: list[str] = []
    for column in df.columns:
        name = str(column).strip().lower()
        if name in aliases or any(name.startswith(f"{alias}.") for alias in aliases):
            matches.append(column)
    return matches


def first_non_empty(row: pd.Series, columns: list[str], default: str = "") -> str:
    for column in columns:
        value = clean_value(row.get(column, ""))
        if value:
            return value
    return default


def normalize_category(category: str) -> str:
    value = clean_value(category)
    return value if value else "Autre"


def normalize_image_source(image_value: str) -> str:
    value = clean_value(image_value)
    if not value:
        return ""
    if value.startswith(("http://", "https://", "/images/")):
        return value
    normalized = value.replace("\\", "/")
    if normalized.startswith("data/images/"):
        normalized = normalized.removeprefix("data/images/")
    if normalized.startswith("images/"):
        normalized = normalized.removeprefix("images/")
    return f"/images/{normalized.lstrip('/')}"


def shorten(text: str, limit: int = 180) -> str:
    value = re.sub(r"\s+", " ", clean_value(text)).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def parse_sort_date(value: str) -> pd.Timestamp:
    text = clean_value(value)
    if not text:
        return pd.NaT

    normalized = text[:10]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return pd.Timestamp(datetime.strptime(normalized, fmt))
        except ValueError:
            continue
    return pd.NaT


def category_slug(category: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", clean_value(category))
    slug = slug.strip("_")
    return slug or "categorie"


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data.columns = [str(column).strip() for column in data.columns]

    title_cols = find_columns(data, "title", "titre")
    source_cols = find_columns(data, "source")
    date_cols = find_columns(data, "date")
    category_cols = find_columns(data, "category", "categorie", "discipline")
    summary_cols = find_columns(data, "summary", "resume")
    url_cols = find_columns(data, "url", "lien")
    image_cols = find_columns(data, "image", "image_url")
    caption_cols = find_columns(data, "image_caption", "caption")
    credibility_cols = find_columns(data, "credibility")

    normalized_rows: list[dict[str, str]] = []
    for _, row in data.iterrows():
        title = polish_text(first_non_empty(row, title_cols))
        source = polish_text(first_non_empty(row, source_cols))
        category = normalize_category(polish_text(first_non_empty(row, category_cols, "Autre")))
        date_value = first_non_empty(row, date_cols)
        summary = polish_text(first_non_empty(row, summary_cols))
        url = first_non_empty(row, url_cols)
        image = normalize_image_source(first_non_empty(row, image_cols))
        image_caption = polish_text(first_non_empty(row, caption_cols))
        credibility = first_non_empty(row, credibility_cols)

        if not title:
            continue

        if not summary or summary == title:
            summary = shorten(title, 200)

        normalized_rows.append(
            {
                "title": title,
                "source": source or "Source inconnue",
                "date": date_value,
                "category": category,
                "summary": summary,
                "url": url,
                "image": image,
                "image_caption": image_caption,
                "credibility": credibility,
            }
        )

    normalized = pd.DataFrame(normalized_rows)
    if normalized.empty:
        return normalized

    normalized["sort_date"] = normalized["date"].apply(parse_sort_date)
    normalized["has_image"] = normalized["image"].apply(bool)
    normalized = normalized.sort_values(
        by=["sort_date", "has_image", "title"],
        ascending=[False, False, True],
        kind="stable",
    )
    normalized = normalized.drop_duplicates(subset=["title", "source", "url"], keep="first")
    return normalized.reset_index(drop=True)


def build_daily_summary(category: str, cat_df: pd.DataFrame) -> str:
    count = len(cat_df)
    if count == 0:
        return f"Aucun article disponible aujourd'hui pour {category}."

    titles = list(OrderedDict.fromkeys(cat_df["title"].tolist()))
    sources = list(OrderedDict.fromkeys(cat_df["source"].tolist()))

    parts = [f"{count} article{'s' if count > 1 else ''} suivi{'s' if count > 1 else ''} aujourd'hui dans {category}."]
    if titles:
        parts.append(f"Temps fort: {shorten(titles[0], 110)}.")
    if len(titles) > 1:
        parts.append(f"Autre sujet marquant: {shorten(titles[1], 110)}.")
    if sources:
        parts.append(f"Sources les plus presentes: {', '.join(sources[:3])}.")
    return " ".join(parts)


def build_kpi_items(cat_df: pd.DataFrame) -> list[tuple[str, str]]:
    article_count = str(len(cat_df))
    source_count = str(cat_df["source"].nunique())
    image_count = str(int(cat_df["image"].apply(bool).sum()))

    credibility_values = pd.to_numeric(cat_df["credibility"], errors="coerce").dropna()
    credibility = f"{credibility_values.mean():.1f}/5" if not credibility_values.empty else "N/A"

    return [
        ("Articles", article_count),
        ("Sources", source_count),
        ("Images", image_count),
        ("Fiabilite moyenne", credibility),
    ]


def render_media(image: str, title: str, category: str) -> str:
    if image:
        alt = html.escape(title or category, quote=True)
        return (
            f'<div class="media"><img src="{html.escape(image, quote=True)}" alt="{alt}" '
            'loading="lazy" onerror="this.closest(\'.media\').classList.add(\'media-fallback\'); this.remove();">'
            f'<span class="media-placeholder">{html.escape(category[:1] or "A")}</span></div>'
        )
    return f'<div class="media media-fallback"><span class="media-placeholder">{html.escape(category[:1] or "A")}</span></div>'


def render_article_card(article: dict[str, str]) -> str:
    title = html.escape(article["title"])
    source = html.escape(article["source"])
    date_value = html.escape(clean_value(article["date"]) or "Date non renseignee")
    summary = html.escape(shorten(article["summary"], 260))
    category = html.escape(article["category"])
    credibility = html.escape(clean_value(article["credibility"]) or "N/A")
    url = html.escape(clean_value(article["url"]) or "#", quote=True)
    link_attrs = ' target="_blank" rel="noopener noreferrer"' if url != "#" else ""

    return f"""
        <article class="article-card">
            {render_media(article["image"], article["title"], article["category"])}
            <div class="article-body">
                <div class="chip-row">
                    <span class="chip chip-category">{category}</span>
                    <span class="chip">{date_value}</span>
                    <span class="chip">Fiabilite {credibility}</span>
                </div>
                <h3><a href="{url}"{link_attrs}>{title}</a></h3>
                <p class="article-source">{source}</p>
                <p class="article-summary">{summary}</p>
                <a class="article-link" href="{url}"{link_attrs}>Lire l'article</a>
            </div>
        </article>
    """


BASE_CSS = """
    :root {
        --bg: #08090e;
        --panel: #11131d;
        --panel-2: #181b27;
        --panel-3: #202536;
        --border: rgba(255, 255, 255, 0.08);
        --text: #eef0f7;
        --muted: #9aa0b8;
        --soft: #6f7694;
        --fire: #ff4c00;
        --gold: #ffb800;
        --ice: #4ec9f7;
        --lime: #7ee080;
        --shadow: 0 20px 45px rgba(0, 0, 0, 0.35);
    }

    * {
        box-sizing: border-box;
    }

    body {
        margin: 0;
        font-family: "Segoe UI", Arial, sans-serif;
        color: var(--text);
        background:
            radial-gradient(circle at top right, rgba(255, 184, 0, 0.12), transparent 24%),
            radial-gradient(circle at top left, rgba(78, 201, 247, 0.14), transparent 26%),
            linear-gradient(180deg, #05060a 0%, #0c1019 100%);
        min-height: 100vh;
    }

    a {
        color: inherit;
        text-decoration: none;
    }

    .page {
        max-width: 1260px;
        margin: 0 auto;
        padding: 32px 20px 72px;
    }

    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 28px;
    }

    .back-link {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 14px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid var(--border);
        color: var(--muted);
    }

    .hero {
        background: linear-gradient(135deg, rgba(255, 76, 0, 0.18), rgba(78, 201, 247, 0.12));
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: var(--shadow);
        border-radius: 24px;
        padding: 28px;
        margin-bottom: 28px;
    }

    .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.05);
        color: var(--gold);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    h1 {
        margin: 18px 0 10px;
        font-size: clamp(2rem, 4vw, 3.3rem);
        line-height: 1.05;
    }

    .hero p {
        max-width: 920px;
        color: var(--muted);
        line-height: 1.7;
        font-size: 1rem;
    }

    .meta-line {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 18px;
        color: var(--soft);
        font-size: 0.92rem;
    }

    .kpi-grid,
    .report-grid,
    .article-grid {
        display: grid;
        gap: 18px;
    }

    .kpi-grid {
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        margin-bottom: 28px;
    }

    .kpi-card,
    .report-card,
    .article-card {
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.015));
        border: 1px solid var(--border);
        border-radius: 20px;
        box-shadow: var(--shadow);
    }

    .kpi-card {
        padding: 20px;
    }

    .kpi-label {
        font-size: 0.82rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }

    .kpi-value {
        font-size: 2rem;
        font-weight: 800;
    }

    .section-title {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        margin: 30px 0 18px;
    }

    .section-title h2 {
        margin: 0;
        font-size: 1.4rem;
    }

    .section-title p {
        margin: 0;
        color: var(--muted);
        font-size: 0.92rem;
    }

    .report-grid {
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    }

    .report-card {
        display: flex;
        flex-direction: column;
        padding: 22px;
        gap: 14px;
    }

    .report-card h3 {
        margin: 0;
        font-size: 1.18rem;
    }

    .report-card p {
        margin: 0;
        color: var(--muted);
        line-height: 1.6;
    }

    .stat-row,
    .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 7px 11px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.05);
        color: var(--muted);
        font-size: 0.8rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .chip-category {
        color: #fff;
        background: rgba(255, 76, 0, 0.18);
        border-color: rgba(255, 76, 0, 0.3);
    }

    .report-link,
    .article-link {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        margin-top: auto;
        padding: 11px 14px;
        border-radius: 12px;
        font-weight: 700;
    }

    .report-link {
        background: rgba(255, 184, 0, 0.12);
        border: 1px solid rgba(255, 184, 0, 0.28);
        color: var(--gold);
    }

    .article-grid {
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    }

    .article-card {
        overflow: hidden;
    }

    .media {
        position: relative;
        height: 210px;
        background: linear-gradient(135deg, rgba(255, 76, 0, 0.22), rgba(78, 201, 247, 0.18));
    }

    .media img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }

    .media.media-fallback {
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .media-placeholder {
        display: inline-flex;
        width: 72px;
        height: 72px;
        border-radius: 50%;
        align-items: center;
        justify-content: center;
        background: rgba(255, 255, 255, 0.08);
        color: #fff;
        font-size: 1.9rem;
        font-weight: 800;
        border: 1px solid rgba(255, 255, 255, 0.12);
        position: absolute;
        inset: 0;
        margin: auto;
    }

    .article-body {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 20px;
    }

    .article-body h3 {
        margin: 0;
        font-size: 1.16rem;
        line-height: 1.4;
    }

    .article-source {
        margin: 0;
        color: var(--ice);
        font-weight: 600;
    }

    .article-summary {
        margin: 0;
        color: var(--muted);
        line-height: 1.65;
        flex: 1;
    }

    .article-link {
        width: fit-content;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid var(--border);
        color: var(--text);
    }

    .empty-state {
        padding: 26px;
        border-radius: 18px;
        border: 1px dashed rgba(255, 255, 255, 0.16);
        color: var(--muted);
        text-align: center;
        background: rgba(255, 255, 255, 0.02);
    }

    @media (max-width: 720px) {
        .page {
            padding: 20px 14px 48px;
        }

        .hero,
        .report-card,
        .kpi-card {
            border-radius: 18px;
        }

        .topbar {
            flex-direction: column;
            align-items: flex-start;
        }
    }
"""


def generate_category_report(cat_df: pd.DataFrame, category: str, date_str: str, today_label: str) -> str:
    cat_id = category_slug(category)
    html_file = REPORTS_DIR / f"{cat_id}_{date_str}.html"
    latest_file = REPORTS_DIR / f"{cat_id}_latest.html"

    summary = build_daily_summary(category, cat_df)
    kpis = "".join(
        f'<div class="kpi-card"><div class="kpi-label">{html.escape(label)}</div>'
        f'<div class="kpi-value">{html.escape(value)}</div></div>'
        for label, value in build_kpi_items(cat_df)
    )
    article_cards = "\n".join(render_article_card(article) for article in cat_df.to_dict("records"))

    page_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport {html.escape(category)} - {today_label}</title>
    <style>
{BASE_CSS}
    </style>
</head>
<body>
    <main class="page">
        <div class="topbar">
            <a class="back-link" href="index_latest.html">Retour a l'index des rapports</a>
        </div>

        <section class="hero">
            <span class="eyebrow">Rapport quotidien</span>
            <h1>{html.escape(category)}</h1>
            <p>{html.escape(summary)}</p>
            <div class="meta-line">
                <span>Date de generation: {html.escape(today_label)}</span>
                <span>Fichier: {html.escape(html_file.name)}</span>
            </div>
        </section>

        <section class="kpi-grid">
            {kpis}
        </section>

        <div class="section-title">
            <h2>Articles du jour</h2>
            <p>Presentation en cartes avec image, resume et acces direct a la source.</p>
        </div>

        <section class="article-grid">
            {article_cards or '<div class="empty-state">Aucun article disponible pour cette categorie.</div>'}
        </section>
    </main>
</body>
</html>
"""

    html_file.write_text(page_html, encoding="utf-8")
    shutil.copy(html_file, latest_file)
    return str(html_file)


def get_default_articles_file() -> Path | None:
    for file_name in ("verified_articles.csv", "organized_articles.csv"):
        candidate = DATA_DIR / file_name
        if candidate.exists():
            return candidate
    return None


def generate_daily_report(articles_csv: str | Path) -> dict | None:
    articles_path = Path(articles_csv)
    if not articles_path.exists():
        print(f"Fichier non trouve : {articles_path}")
        return None

    df = pd.read_csv(articles_path)
    df = normalize_dataframe(df)
    if df.empty:
        print("Aucun article exploitable pour la generation des rapports.")
        return None

    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    today_label = now.strftime("%d/%m/%Y")

    categories = [
        category
        for category in df["category"].fillna("Autre").tolist()
        if category
    ]
    ordered_categories = list(OrderedDict.fromkeys(categories))

    report_cards = []
    for category in ordered_categories:
        cat_df = df[df["category"] == category].copy()
        if cat_df.empty:
            continue
        generate_category_report(cat_df, category, date_str, today_label)
        report_cards.append(
            {
                "category": category,
                "count": len(cat_df),
                "summary": build_daily_summary(category, cat_df),
                "link": f"{category_slug(category)}_latest.html",
                "sources": int(cat_df["source"].nunique()),
            }
        )

    report_cards.sort(key=lambda item: item["count"], reverse=True)

    cards_html = "\n".join(
        f"""
        <article class="report-card">
            <div class="stat-row">
                <span class="chip chip-category">{html.escape(card["category"])}</span>
                <span class="chip">{card["count"]} article{'s' if card["count"] > 1 else ''}</span>
                <span class="chip">{card["sources"]} source{'s' if card["sources"] > 1 else ''}</span>
            </div>
            <h3>{html.escape(card["category"])}</h3>
            <p>{html.escape(shorten(card["summary"], 240))}</p>
            <a class="report-link" href="{html.escape(card["link"], quote=True)}">Ouvrir le rapport</a>
        </article>
        """
        for card in report_cards
    )

    index_file = REPORTS_DIR / f"index_{date_str}.html"
    index_latest = REPORTS_DIR / "index_latest.html"

    index_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Index des rapports - {today_label}</title>
    <style>
{BASE_CSS}
    </style>
</head>
<body>
    <main class="page">
        <div class="topbar">
            <a class="back-link" href="/">Retour au tableau de bord</a>
        </div>

        <section class="hero">
            <span class="eyebrow">Veille sportive</span>
            <h1>Rapports quotidiens par categorie</h1>
            <p>
                Chaque categorie dispose d'un rapport propre avec une synthese du jour,
                des indicateurs rapides et les articles presentes sous forme de cartes.
            </p>
            <div class="meta-line">
                <span>Genere le {html.escape(today_label)}</span>
                <span>Source de donnees: {html.escape(articles_path.name)}</span>
            </div>
        </section>

        <div class="section-title">
            <h2>Categories disponibles</h2>
            <p>{len(report_cards)} rapport{'s' if len(report_cards) > 1 else ''} genere{'s' if len(report_cards) > 1 else ''} aujourd'hui.</p>
        </div>

        <section class="report-grid">
            {cards_html or '<div class="empty-state">Aucun rapport disponible.</div>'}
        </section>
    </main>
</body>
</html>
"""

    index_file.write_text(index_html, encoding="utf-8")
    shutil.copy(index_file, index_latest)

    print(f"Rapports generes dans {REPORTS_DIR}")
    return {
        "html": str(index_latest),
        "categories": [card["category"] for card in report_cards],
        "count": len(report_cards),
        "source_file": str(articles_path),
    }


if __name__ == "__main__":
    default_file = get_default_articles_file()
    if default_file:
        generate_daily_report(default_file)
    else:
        print("Aucun fichier CSV d'articles disponible.")
