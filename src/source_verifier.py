"""
source_verifier.py — Evaluation et vérification de crédibilité des sources financières
MarketPulse — Supporte les sources financières internationales (EN / FR / AR)
"""

import pandas as pd
import os

# ─────────────────────────────────────────────
# BARÈME DE CRÉDIBILITÉ FINANCIÈRE (1-5 ÉTOILES)
# Basé sur : Réputation de domaine, audit éditorial, fiabilité des données de marché
# ─────────────────────────────────────────────
FINANCIAL_TRUSTED_SOURCES = {
    # ── 5 étoiles — Institutions & Agences Financières de Référence ──
    "Financial Times":         5,
    "Wall Street Journal":    5,
    "The Economist":           5,
    "Reuters":                 5,
    "Bloomberg":               5,
    "Les Échos":               5,
    "CNBC Markets":            5,
    "Harvard Business Review": 5,

    # ── 4 étoiles — Médias Financiers Majeurs ──
    "Yahoo Finance":           4,
    "MarketWatch":             4,
    "BFM Business":            4,
    "La Tribune":              4,
    "Le Figaro Économie":      4,
    "Boursorama":              4,
    "Investing.com":           4,
    "Seeking Alpha":           4,
    "Benzinga":                4,
    "L'Usine Nouvelle":        4,
    "Business Insider":        4,
    "CoinDesk":                4,
    "TechCrunch Finance":      4,

    # ── 3 étoiles — Presse Économique Régionale & Spécialisée ──
    "Hespress Économie":       3,
    "Médias24":                3,
    "Boursenews":              3,
    "Argaam":                  3,
    "Le360 Économie":          3,
    "Maddyness":               3,
    "CoinTelegraph":           3,
    "Cryptoast":               3,
    "Decrypt":                 3,

    # Score par défaut pour autres sources
}

DEFAULT_SCORE = 3


def get_credibility(source_name: str) -> int:
    """Retourne le score de crédibilité d'une source financière (1 à 5)."""
    if not source_name:
        return DEFAULT_SCORE

    if source_name in FINANCIAL_TRUSTED_SOURCES:
        return FINANCIAL_TRUSTED_SOURCES[source_name]

    source_lower = source_name.lower()
    for known, score in FINANCIAL_TRUSTED_SOURCES.items():
        if known.lower() in source_lower or source_lower in known.lower():
            return score

    return DEFAULT_SCORE


def verify_sources(input_path: str, output_path: str) -> pd.DataFrame:
    """Enrichit le fichier CSV avec les scores de crédibilité financière."""
    print(f"📂 Lecture des actualités financières : {input_path}")
    df = pd.read_csv(input_path, encoding="utf-8-sig")

    df.columns = [c.strip().lower() for c in df.columns]
    col_map = {
        "titre": "title", "title": "title",
        "source": "source",
        "categorie": "category", "category": "category",
        "date": "date",
        "resume": "summary", "summary": "summary",
        "url": "url", "lien": "url",
        "lang": "lang",
        "image_url": "image_url",
        "image_caption": "image_caption",
        "sentiment": "sentiment",
    }
    df = df.rename(columns={c: col_map.get(c, c) for c in df.columns})

    df["credibility"] = df["source"].apply(get_credibility)

    print(f"\n📊 Rapport de crédibilité des sources financières ({len(df)} articles) :")
    print(f"\n   {'Source Financière':30s} | {'Crédibilité':12s} | {'Articles':8s}")
    print("   " + "-" * 56)

    if not df.empty:
        stats = df.groupby(["source", "credibility"]).size().reset_index(name="count")
        stats = stats.sort_values("credibility", ascending=False)
        for _, row in stats.iterrows():
            stars = "★" * int(row["credibility"]) + "☆" * (5 - int(row["credibility"]))
            print(f"   {row['source']:30s} | {stars:12s} | {int(row['count']):4d}")

        avg = df["credibility"].mean()
        print(f"\n   Crédibilité moyenne du flux : {avg:.2f}/5")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n✅ Sauvegardé : {output_path}")
    return df


if __name__ == "__main__":
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inp = os.path.join(BASE, "data", "output", "articles_test.csv")
    out = os.path.join(BASE, "data", "output", "verified_articles.csv")

    if os.path.exists(inp):
        verify_sources(inp, out)
