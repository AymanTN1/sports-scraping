"""
ai_organizer.py - MarketPulse NLP Engine
1. Classification multilingue des articles financiers (Bourse, Macro, Crypto, Immobilier, Fintech, Startups/VC)
2. Analyse de Sentiment Financier (Bullish, Bearish, Neutre)
"""

from __future__ import annotations

import os
import re
import unicodedata
from urllib.parse import unquote
import pandas as pd

# ─────────────────────────────────────────────
# DICTIONNAIRE MULTILINGUE DE CATÉGORIES FINANCIÈRES
# ─────────────────────────────────────────────
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Bourse & Actions": [
        "bourse", "actions", "action", "dividende", "dividendes", "cac 40", "cac40", "nasdaq", "dow jones", "s&p 500", "sp500",
        "wall street", "marché boursier", "marchés boursiers", "earnings", "résultats financiers", "chiffre d'affaires", "profit",
        "market cap", "capitalisation", "valuation", "shares", "stocks", "stock market", "trading", "trader", "traders",
        "equity", "equities", "nyse", "nikkei", "ftse", "dax", "investisseurs", "investisseur", "investors", "shareholder",
        "أسهم", "بورصة", "تداول", "مؤشر", "سوق الأسهم", "أرباح", "عائدات", "الأسواق المالية",
    ],
    "Macroéconomie": [
        "macroéconomie", "macroéconomie", "inflation", "déflation", "banque centrale", "fed", "bce", "bce", "réserve fédérale",
        "taux d'intérêt", "taux d'interet", "pib", "gdp", "croissance", "récession", "recession", "dette publique", "déficit",
        "emploi", "chômage", "politique monétaire", "monetary policy", "interest rates", "rate hike", "central bank", "jerome powell",
        "lagarde", "bce", "économie", "economie", "economy", "trade war", "tarif", "tarifs", "douanes",
        "التضخم", "البنك المركزي", "الفائدة", "النمو الاقتصادي", "الركود", "الدين العام", "الاقتصاد العالمي",
    ],
    "Cryptomonnaies": [
        "crypto", "cryptomonnaie", "cryptomonnaies", "cryptocurrency", "cryptocurrencies", "bitcoin", "btc", "ethereum", "eth",
        "solana", "sol", "blockchain", "altcoin", "altcoins", "binance", "coinbase", "sec", "sec crypto", "defi", "web3",
        "token", "tokens", "wallet", "minage", "mining", "halving", "bull run", "bear market crypto", "stablecoin", "usdt", "usdc",
        "البيتكوين", "العملات الرقمية", "كريبتو", "بلوكشين", "إيثريوم", "تشفير",
    ],
    "Immobilier": [
        "immobilier", "marché immobilier", "crédit immobilier", "taux immobilier", "taux d'emprunt", "logement", "logements",
        "real estate", "housing market", "mortgage", "mortgages", "property", "properties", "reit", "reits", "prix au m2",
        "حافلة عقارية", "عقارات", "السوق العقاري", "القروض العقارية", "الإسكان",
    ],
    "Banque & Fintech": [
        "banque", "banques", "banking", "bank", "banks", "fintech", "fintechs", "néobanque", "neobank", "paiement", "payments",
        "visa", "mastercard", "paypal", "stripe", "revolut", "swift", "open banking", "régulation bancaire", "crédit", "prêt",
        "البنوك", "مصرف", "مصرفية", "تكنولوجيا مالية", "فينتك", "الدفع الإلكتروني",
    ],
    "Startups & VC": [
        "startup", "startups", "venture capital", "vc", "levée de fonds", "levee de fonds", "fundraising", "fundraise",
        "licorne", "licornes", "unicorn", "unicorns", "seed", "series a", "series b", "fondateur", "founders", "pitch",
        "incubateur", "accélérateur", "valorisation", "venture", "business angel",
        "الشركات الناشئة", "تمويل", "رأس المال الاستثماري", "استثمار",
    ],
}

# ─────────────────────────────────────────────
# MOTEUR D'ANALYSE DE SENTIMENT FINANCIER
# ─────────────────────────────────────────────
BULLISH_KEYWORDS = [
    # Français
    "hausse", "rebond", "surge", "bénéfice", "bénéfices", "profit", "profits", "records", "record", "croissance", "progression",
    "envolée", "gain", "gains", "surpasse", "positif", "optimisme", "reprise", "dividend", "dividendes", "plus-value",
    # English
    "bullish", "surging", "surged", "rally", "rallies", "rallied", "jump", "jumps", "jumped", "soar", "soars", "soared",
    "gain", "gains", "gained", "outperform", "outperformed", "beat", "beats", "record high", "growth", "expansion",
    # Arabe
    "ارتفاع", "صعود", "أرباح", "نمو", "انتعاش", "مكاسب", "قياسي", "إيجابي", "تفوق",
]

BEARISH_KEYWORDS = [
    # Français
    "chute", "chutes", "baisse", "baisses", "recul", "plonge", "plongée", "déficit", "deficit", "perte", "pertes", "faillite",
    "crise", "effondrement", "inflation", "récession", "recession", "licenciements", "menace", "plongeon", "inquietude",
    # English
    "bearish", "plunge", "plunges", "plunged", "slump", "slumps", "slumped", "drop", "drops", "dropped", "fall", "falls",
    "fell", "crash", "crashes", "crashed", "loss", "losses", "bankruptcy", "bankrupt", "layoffs", "layoff", "decline",
    "recession", "crisis", "default", "selloff", "sell-off",
    # Arabe
    "انخفاض", "تراجع", "خسائر", "خسارة", "أزمة", "ركود", "إفلاس", "انهيار", "سلبي", "هبوط",
]


def normalize_text(text: str) -> str:
    """Normalise le texte pour le matching NLP."""
    if not text:
        return ""
    text = unquote(str(text))
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def classify_article(article: dict) -> str:
    """Classifie un article dans une catégorie financière."""
    title = str(article.get("title", ""))
    summary = str(article.get("summary", ""))
    src_cat = str(article.get("category", ""))

    text = f"{title} {summary}".lower()

    # Match exact
    category_scores: dict[str, int] = {cat: 0 for cat in CATEGORY_KEYWORDS}

    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                category_scores[cat] += 2 if kw.lower() in title.lower() else 1

    best_cat = max(category_scores, key=category_scores.get)
    if category_scores[best_cat] > 0:
        return best_cat

    # Priorité catégorie par défaut du scraper si trouvée
    if src_cat in CATEGORY_KEYWORDS:
        return src_cat

    return "Macroéconomie"


def analyze_sentiment(article: dict) -> str:
    """Analyse le sentiment financier d'un article : Bullish (+1), Bearish (-1), ou Neutre (0)."""
    title = str(article.get("title", ""))
    summary = str(article.get("summary", ""))
    text = f"{title} {summary}".lower()

    bullish_score = sum(2 if kw in title.lower() else 1 for kw in BULLISH_KEYWORDS if kw in text)
    bearish_score = sum(2 if kw in title.lower() else 1 for kw in BEARISH_KEYWORDS if kw in text)

    if bullish_score > bearish_score and bullish_score >= 1:
        return "Bullish"
    elif bearish_score > bullish_score and bearish_score >= 1:
        return "Bearish"
    else:
        return "Neutre"


def process_articles_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Enrichit un DataFrame d'articles avec la classification et l'analyse de sentiment."""
    if df.empty:
        return df

    categories = []
    sentiments = []
    for _, row in df.iterrows():
        art = row.to_dict()
        cat = classify_article(art)
        sent = analyze_sentiment(art)
        categories.append(cat)
        sentiments.append(sent)

    df["category"] = categories
    df["sentiment"] = sentiments
    return df


if __name__ == "__main__":
    test_arts = [
        {"title": "Bitcoin surges past $90,000 as crypto market rallies", "summary": "Record highs for BTC"},
        {"title": "Fed raises interest rates amid rising inflation concerns", "summary": "Powell signals hawkish tone"},
        {"title": "Les résultats d'LVMH en forte baisse au premier trimestre", "summary": "Chute du chiffre d'affaires"},
        {"title": "Stripe annonce une nouvelle levée de fonds de 500M$", "summary": "Fintech unicorn expansion"},
    ]
    for a in test_arts:
        print(f"[{classify_article(a)}] [{analyze_sentiment(a)}] {a['title']}")
