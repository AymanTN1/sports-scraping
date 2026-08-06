"""
ai_organizer.py — MercatoPulse Football Transfer & Mercato NLP Engine
1. Classification des articles par Championnat/Ligue (Premier League, La Liga, Ligue 1, Serie A, Bundesliga, Saudi Pro League, etc.)
2. Extraction d'entités Mercato (Joueurs, Club Vendeur, Club Acheteur, Montant du Transfert, Statut du Transfert)
3. Analyse de Statut : OFFICIEL ✅, HERE WE GO 🔥, NEGOCIATION 💬, RUMEUR 📰
"""

from __future__ import annotations

import os
import re
import unicodedata
from urllib.parse import unquote
import pandas as pd

# ─────────────────────────────────────────────
# LIGUES & CHAMPIONNATS FOOTBALL
# ─────────────────────────────────────────────
LEAGUE_KEYWORDS: dict[str, list[str]] = {
    "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿": [
        "premier league", "manchester city", "man city", "arsenal", "liverpool", "manchester united", "man utd",
        "chelsea", "tottenham", "spurs", "newcastle", "aston villa", "west ham", "brighton", "everton", "brentford",
        "crystal palace", "wolverhampton", "wolves", "fulham", "bournemouth", "nottingham forest", "england", "angletterre"
    ],
    "La Liga 🇪🇸": [
        "la liga", "la liga santander", "real madrid", "barcelona", "barça", "fc barcelone", "atletico madrid",
        "atlético", "sevilla", "séville", "real betis", "villareal", "athletic bilbao", "real sociedad", "girona", "espagne"
    ],
    "Ligue 1 🇫🇷": [
        "ligue 1", "psg", "paris saint-germain", "olympique de marseille", "om", "olympique lyonnais", "ol", "lyon",
        "monaco", "as monaco", "lille", "losc", "rennes", "stade rennais", "nice", "ogc nice", "lens", "rc lens",
        "strasbourg", "nantes", "toulouse", "france", "ligue1"
    ],
    "Serie A 🇮🇹": [
        "serie a", "inter milan", "inter", "ac milan", "juventus", "juve", "napoli", "naples", "roma", "as roma",
        "lazio", "atala", "atalanta", "fiorentina", "bologna", "italie", "italy"
    ],
    "Bundesliga 🇩🇪": [
        "bundesliga", "bayern munich", "bayern", "borussia dortmund", "dortmund", "bvb", "bayer leverkusen",
        "leverkusen", "rb leipzig", "leipzig", "eintracht frankfurt", "stuttgart", "allemagne", "germany"
    ],
    "Saudi Pro League 🇸🇦": [
        "saudi pro league", "al nassr", "al-nassr", "al hilal", "al-hilal", "al ittihad", "al-ittihad",
        "al ahli", "al-ahli", "saudi", "arabie saoudite", "saudi league"
    ],
    "Champions League 🇪🇺": [
        "champions league", "ligue des champions", "c1", "uefa", "europa league", "conference league"
    ],
}

# ─────────────────────────────────────────────
# JOUEURS & CLUBS MAJEURS MERCATO
# ─────────────────────────────────────────────
KNOWN_PLAYERS = [
    "Kylian Mbappé", "Erling Haaland", "Lamine Yamal", "Jude Bellingham", "Vinicius Jr", "Victor Osimhen",
    "Florian Wirtz", "Mohamed Salah", "Achraf Hakimi", "Ousmane Dembélé", "Kevin De Bruyne", "Luka Modric",
    "Antoine Griezmann", "Neymar", "Cristiano Ronaldo", "Lionel Messi", "Marcus Rashford", "Alexander Isak",
    "Bruno Fernandes", "Gianluigi Donnarumma", "Lautaro Martinez", "Harry Kane", "Bukayo Saka", "Pedri",
    "Gavi", "Endrick", "Estevao", "Viktor Gyökeres", "Federico Valverde", "Eduardo Camavinga", "Aurélien Tchouaméni",
    "Rodrygo", "Julian Alvarez", "Cole Palmer", "Trent Alexander-Arnold", "Virgil van Dijk", "Mason Greenwood",
    "Joao Neves", "Leny Yoro", "Khvicha Kvaratskhelia", "Rafael Leao", "Theo Hernandez", "Michael Olise",
    "Joshua Kimmich", "Alphonso Davies", "Jamal Musiala", "Xavi Simons", "Nico Williams", "Dani Olmo"
]

KNOWN_CLUBS = [
    "Real Madrid", "FC Barcelone", "PSG", "Manchester City", "Arsenal", "Liverpool", "Manchester United",
    "Chelsea", "Bayern Munich", "Juventus", "Inter Milan", "AC Milan", "Atlético de Madrid", "Bayer Leverkusen",
    "Borussia Dortmund", "Al-Nassr", "Al-Hilal", "Al-Ittihad", "AS Monaco", "Olympique de Marseille", "Olympique Lyonnais"
]

# ─────────────────────────────────────────────
# REGEX DETECTION DE MONTANTS (Ex: 85M€, 100M$, Gratuit, Prêt)
# ─────────────────────────────────────────────
FEE_PATTERNS = [
    r"(\d+[\.,]?\d*\s*(?:M€|millions?|M\$|M£|M€|millions d'euros))",
    r"(gratuit|fin de contrat|free transfer)",
    r"(prêt avec option|prêt|loan)",
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
    """Classifie l'article par Championnat/Ligue."""
    title = str(article.get("title", ""))
    summary = str(article.get("summary", ""))
    src_cat = str(article.get("category", ""))
    full_text = f"{title} {summary} {src_cat}".lower()

    scores = {league: 0 for league in LEAGUE_KEYWORDS}

    for league, keywords in LEAGUE_KEYWORDS.items():
        for kw in keywords:
            if kw in full_text:
                scores[league] += 2 if kw in title.lower() else 1

    best_league = max(scores, key=scores.get)
    if scores[best_league] > 0:
        return best_league

    return "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿"


def detect_status(title: str, summary: str) -> str:
    """Détermine le statut du transfert (Officiel, Here We Go, Négociation, Rumeur)."""
    text = f"{title} {summary}".lower()
    
    if any(k in text for k in ["officiel", "official", "signé", "signed", "done deal", "accord officiel", "confirmé", "s'engage avec"]):
        return "OFFICIEL ✅"
    if any(k in text for k in ["here we go", "imminent", "visite médicale", "medical", "accord trouvé", "agreement reached"]):
        return "HERE WE GO 🔥"
    if any(k in text for k in ["négociation", "negociation", "talks", "offre de", "offer", "discutent", "en discussions"]):
        return "NEGOCIATION 💬"
    
    return "RUMEUR 📰"


def extract_mercato_entities(title: str, summary: str) -> dict:
    """Extrait le joueur, le club vendeur/acheteur, le montant et le statut."""
    full_text = f"{title} {summary}"
    
    # 1. Player
    player = None
    for p in KNOWN_PLAYERS:
        if p.lower() in full_text.lower():
            player = p
            break
            
    # 2. Clubs
    clubs_found = []
    for c in KNOWN_CLUBS:
        if c.lower() in full_text.lower():
            clubs_found.append(c)
            
    from_club = clubs_found[0] if len(clubs_found) > 0 else "Club Acquéreur / Vendeur"
    to_club = clubs_found[1] if len(clubs_found) > 1 else clubs_found[0] if len(clubs_found) == 1 else "Club Cible"
    
    # 3. Fee
    fee = "Non communiqué"
    for pat in FEE_PATTERNS:
        match = re.search(pat, full_text, re.IGNORECASE)
        if match:
            fee = match.group(1).title()
            break
            
    # 4. Status
    status = detect_status(title, summary)
    
    return {
        "player_name": player or "Joueur Vise",
        "from_club": from_club,
        "to_club": to_club,
        "transfer_fee": fee,
        "status": status,
    }


def analyze_sentiment(title: str, summary: str) -> str:
    """Détermine la tendance/Hype de l'information Mercato."""
    text = f"{title} {summary}".lower()
    
    if any(k in text for k in ["accord", "hot", "brûlant", "signe", "proche", "top", "avance", "record"]):
        return "Bullish"
    elif any(k in text for k in ["capote", "refus", "bloqué", "rejeté", "blessure", "échec", "froid"]):
        return "Bearish"
    
    return "Neutre"


def process_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Traite le DataFrame complet en ajoutant la classification et les entités Mercato."""
    if df.empty:
        return df

    categories = []
    sentiments = []
    players = []
    from_clubs = []
    to_clubs = []
    fees = []
    statuses = []

    for _, row in df.iterrows():
        title = str(row.get("title", ""))
        summary = str(row.get("summary", ""))

        cat = classify_article(row.to_dict())
        sent = analyze_sentiment(title, summary)
        entities = extract_mercato_entities(title, summary)

        categories.append(cat)
        sentiments.append(sent)
        players.append(entities["player_name"])
        from_clubs.append(entities["from_club"])
        to_clubs.append(entities["to_club"])
        fees.append(entities["transfer_fee"])
        statuses.append(entities["status"])

    df["category"] = categories
    df["league"] = categories
    df["sentiment"] = sentiments
    df["player_name"] = players
    df["from_club"] = from_clubs
    df["to_club"] = to_clubs
    df["transfer_fee"] = fees
    df["status"] = statuses

    return df
