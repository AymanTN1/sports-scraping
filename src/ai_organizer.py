"""
ai_organizer.py — MercatoPulse Football Transfer & Mercato NLP Engine
1. Classification des articles par Championnat/Ligue (Premier League, La Liga, Ligue 1, Serie A, Bundesliga, Saudi Pro League, etc.)
2. Extraction d'entités Mercato précises (Joueurs, Club Vendeur, Club Acheteur, Montant du Transfert, Statut du Transfert, Sélection Nationale)
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
        "atlético", "sevilla", "séville", "real betis", "villareal", "villarreal", "athletic bilbao", "real sociedad", "girona", "espagne", "spain"
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
# JOUEURS & SÉLECTIONS NATIONALES
# ─────────────────────────────────────────────
PLAYER_NATIONALITY: dict[str, str] = {
    "Kylian Mbappé": "France 🇫🇷",
    "Erling Haaland": "Norvège 🇳🇴",
    "Lamine Yamal": "Espagne 🇪🇸",
    "Jude Bellingham": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Vinicius Jr": "Brésil 🇧🇷",
    "Victor Osimhen": "Nigéria 🇳🇬",
    "Florian Wirtz": "Allemagne 🇩🇪",
    "Mohamed Salah": "Égypte 🇪🇬",
    "Achraf Hakimi": "Maroc 🇲🇦",
    "Ousmane Dembélé": "France 🇫🇷",
    "Kevin De Bruyne": "Belgique 🇧🇪",
    "Luka Modric": "Croatie 🇭🇷",
    "Antoine Griezmann": "France 🇫🇷",
    "Neymar": "Brésil 🇧🇷",
    "Cristiano Ronaldo": "Portugal 🇵🇹",
    "Lionel Messi": "Argentine 🇦🇷",
    "Marcus Rashford": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Alexander Isak": "Suède 🇸🇪",
    "Bruno Fernandes": "Portugal 🇵🇹",
    "Gianluigi Donnarumma": "Italie 🇮🇹",
    "Lautaro Martinez": "Argentine 🇦🇷",
    "Harry Kane": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Bukayo Saka": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Phil Foden": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Declan Rice": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Cole Palmer": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Pedri": "Espagne 🇪🇸",
    "Gavi": "Espagne 🇪🇸",
    "Rodri": "Espagne 🇪🇸",
    "Nico Williams": "Espagne 🇪🇸",
    "Dani Olmo": "Espagne 🇪🇸",
    "Endrick": "Brésil 🇧🇷",
    "Estevao": "Brésil 🇧🇷",
    "Viktor Gyökeres": "Suède 🇸🇪",
    "Federico Valverde": "Uruguay 🇺🇾",
    "Eduardo Camavinga": "France 🇫🇷",
    "Aurélien Tchouaméni": "France 🇫🇷",
    "William Saliba": "France 🇫🇷",
    "Theo Hernandez": "France 🇫🇷",
    "Michael Olise": "France 🇫🇷",
    "Bradley Barcola": "France 🇫🇷",
    "Warren Zaïre-Emery": "France 🇫🇷",
    "Rodrygo": "Brésil 🇧🇷",
    "Julian Alvarez": "Argentine 🇦🇷",
    "Alexis Mac Allister": "Argentine 🇦🇷",
    "Enzo Fernandez": "Argentine 🇦🇷",
    "Trent Alexander-Arnold": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Virgil van Dijk": "Pays-Bas 🇳🇱",
    "Xavi Simons": "Pays-Bas 🇳🇱",
    "Cody Gakpo": "Pays-Bas 🇳🇱",
    "Frenkie de Jong": "Pays-Bas 🇳🇱",
    "Jamal Musiala": "Allemagne 🇩🇪",
    "Leroy Sané": "Allemagne 🇩🇪",
    "Kai Havertz": "Allemagne 🇩🇪",
    "Joshua Kimmich": "Allemagne 🇩🇪",
    "Rafael Leao": "Portugal 🇵🇹",
    "Bernardo Silva": "Portugal 🇵🇹",
    "Rúben Dias": "Portugal 🇵🇹",
    "Joao Neves": "Portugal 🇵🇹",
    "Leny Yoro": "France 🇫🇷",
    "Khvicha Kvaratskhelia": "Géorgie 🇬🇪",
    "Nicolo Barella": "Italie 🇮🇹",
    "Alessandro Bastoni": "Italie 🇮🇹",
    "Federico Chiesa": "Italie 🇮🇹",
    "Brahim Diaz": "Maroc 🇲🇦",
    "Nayef Aguerd": "Maroc 🇲🇦",
    "Azzedine Ounahi": "Maroc 🇲🇦",
    "Alphonso Davies": "Canada 🇨🇦",
    "Khvicha Kvaratskhelia": "Géorgie 🇬🇪",
}

KNOWN_PLAYERS = list(PLAYER_NATIONALITY.keys())

KNOWN_CLUBS = [
    "Real Madrid", "FC Barcelone", "PSG", "Manchester City", "Arsenal", "Liverpool", "Manchester United",
    "Chelsea", "Bayern Munich", "Juventus", "Inter Milan", "AC Milan", "Atlético de Madrid", "Bayer Leverkusen",
    "Borussia Dortmund", "Al-Nassr", "Al-Hilal", "Al-Ittihad", "AS Monaco", "Olympique de Marseille", "Olympique Lyonnais",
    "Aston Villa", "Newcastle", "Tottenham", "Sporting CP", "Benfica", "FC Porto", "Napoli", "Roma", "West Ham", "Girona"
]

# ─────────────────────────────────────────────
# REGEX DETECTION DE MONTANTS
# ─────────────────────────────────────────────
FEE_PATTERNS = [
    r"(\d+[\.,]?\d*\s*(?:M€|millions?|M\$|M£|millions d'euros|million))",
    r"(gratuit|fin de contrat|free transfer|libre|prêt|loan)",
    r"(clause de \d+[\.,]?\d*\s*M€)",
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


def parse_numeric_fee(fee_str: str) -> float:
    """Extrait le montant numérique en Millions d'€ depuis une chaîne."""
    if not fee_str:
        return 0.0
    s = fee_str.lower()
    if "gratuit" in s or "free" in s or "prêt" in s or "loan" in s or "libre" in s:
        return 0.0
    match = re.search(r"(\d+[\.,]?\d*)", s)
    if match:
        try:
            val = float(match.group(1).replace(",", "."))
            return val
        except ValueError:
            return 0.0
    return 0.0


def analyze_sentiment(title: str, summary: str) -> str:
    """Détermine la tendance/Hype de l'information Mercato."""
    text = f"{title} {summary}".lower()
    if any(k in text for k in ["accord", "hot", "brûlant", "signe", "proche", "top", "avance", "record", "here we go"]):
        return "Bullish"
    elif any(k in text for k in ["capote", "refus", "bloqué", "rejeté", "blessure", "échec", "froid", "avorté"]):
        return "Bearish"
    return "Neutre"


def classify_article(article: dict | str) -> str:
    """Classifie un article selon son championnat/ligue."""
    if isinstance(article, str):
        text = article
    else:
        text = f"{article.get('title', '')} {article.get('summary', '')} {article.get('category', '')}"
    
    norm = normalize_text(text)
    for league, kws in LEAGUE_KEYWORDS.items():
        for kw in kws:
            if kw in norm:
                return league
    return "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿"


def extract_mercato_entities(title: str, summary: str = "") -> dict:
    """
    Extrait intelligemment les entités du transfert à partir du titre et du résumé:
    - Nom du joueur
    - Sélection nationale
    - Club de départ (from_club)
    - Club d'arrivée (to_club)
    - Montant estimé ou officiel
    - Statut (OFFICIEL, HERE WE GO, NEGOCIATION, RUMEUR)
    """
    combined = f"{title} {summary}"
    norm = normalize_text(combined)

    # 1. Joueur
    detected_player = None
    for p in KNOWN_PLAYERS:
        if normalize_text(p) in norm:
            detected_player = p
            break
    
    if not detected_player:
        # Recherche par regex d'un nom propre
        match_p = re.search(r"\b([A-ZÀ-ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-ÿ][a-zà-ÿ]+))\b", title)
        if match_p and match_p.group(1) not in KNOWN_CLUBS:
            detected_player = match_p.group(1)
        else:
            detected_player = "Joueur Star"

    # 2. Nationalité
    nat_team = PLAYER_NATIONALITY.get(detected_player, "International 🌍")

    # 3. Statut
    norm_title = title.lower()
    if any(k in norm_title for k in ["officiel", "official", "signe", "signé", "prolonge", "confirmé"]):
        status = "OFFICIEL ✅"
    elif any(k in norm_title for k in ["here we go", "accord total", "deal done", "visite médicale"]):
        status = "HERE WE GO 🔥"
    elif any(k in norm_title for k in ["négociation", "pourparlers", "offre", "discussions", "proche", "avance"]):
        status = "NEGOCIATION 💬"
    else:
        status = "RUMEUR 📰"

    # 4. Clubs & Direction
    detected_clubs = []
    for c in KNOWN_CLUBS:
        if normalize_text(c) in norm:
            detected_clubs.append(c)

    from_club = "Club Vendeur"
    to_club = "Club Cible"

    if "prolonge" in norm_title:
        # Prolongation au même club
        if detected_clubs:
            from_club = detected_clubs[0]
            to_club = detected_clubs[0]
    elif len(detected_clubs) >= 2:
        # Détection de direction (ex: "du Borussia Dortmund au Real Madrid", "de Napoli vers PSG")
        c1, c2 = detected_clubs[0], detected_clubs[1]
        pos1 = norm.find(normalize_text(c1))
        pos2 = norm.find(normalize_text(c2))

        # Vérifier les prépositions autour
        snippet_before_1 = norm[max(0, pos1-15):pos1]
        snippet_before_2 = norm[max(0, pos2-15):pos2]

        if any(w in snippet_before_1 for w in ["du", "de", "provenance", "quitte"]) or any(w in snippet_before_2 for w in ["au", "vers", "pour", "rejoint", "signe"]):
            from_club, to_club = c1, c2
        elif any(w in snippet_before_2 for w in ["du", "de", "provenance", "quitte"]) or any(w in snippet_before_1 for w in ["au", "vers", "pour", "rejoint", "signe"]):
            from_club, to_club = c2, c1
        else:
            # Ordre d'apparition
            if pos1 < pos2:
                from_club, to_club = c1, c2
            else:
                from_club, to_club = c2, c1
    elif len(detected_clubs) == 1:
        c = detected_clubs[0]
        if any(w in norm_title for w in ["vers", "au", "rejoint", "signe", "viseur"]):
            to_club = c
            from_club = "Club Vendeur"
        elif any(w in norm_title for w in ["quitte", "du", "de"]):
            from_club = c
            to_club = "Club Cible"
        else:
            to_club = c

    # 5. Montant
    fee_str = "Non communiqué"
    for pat in FEE_PATTERNS:
        m = re.search(pat, combined, re.IGNORECASE)
        if m:
            fee_str = m.group(1).strip()
            if "gratuit" in fee_str.lower() or "libre" in fee_str.lower():
                fee_str = "Free / Gratuit"
            break

    numeric_fee = parse_numeric_fee(fee_str)

    return {
        "player_name": detected_player,
        "national_team": nat_team,
        "from_club": from_club,
        "to_club": to_club,
        "transfer_fee": fee_str,
        "fee_numeric": numeric_fee,
        "status": status,
    }


def process_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Traite le DataFrame complet en préservant les données précises et en enrichissant le reste."""
    if df.empty:
        return df

    categories = []
    sentiments = []
    players = []
    national_teams = []
    from_clubs = []
    to_clubs = []
    fees = []
    fee_nums = []
    statuses = []

    for _, row in df.iterrows():
        title = str(row.get("title", ""))
        summary = str(row.get("summary", ""))

        existing_player = str(row.get("player_name", "")).strip()
        existing_from = str(row.get("from_club", "")).strip()
        existing_to = str(row.get("to_club", "")).strip()
        existing_fee = str(row.get("transfer_fee", "")).strip()
        existing_status = str(row.get("status", "")).strip()
        existing_league = str(row.get("category", "") or row.get("league", "")).strip()

        entities = extract_mercato_entities(title, summary)
        cat = existing_league if existing_league and "League" in existing_league or "Liga" in existing_league else classify_article(row.to_dict())
        sent = analyze_sentiment(title, summary)

        # Préserver les valeurs explicites
        final_player = existing_player if existing_player and existing_player not in ["Joueur Target", "Joueur Vise", "Joueur Star", "nan"] else entities["player_name"]
        final_from = existing_from if existing_from and existing_from not in ["Club Vendeur", "Club Acquéreur", "nan"] else entities["from_club"]
        final_to = existing_to if existing_to and existing_to not in ["Club Cible", "nan"] else entities["to_club"]
        final_fee = existing_fee if existing_fee and existing_fee not in ["Non communiqué", "nan"] else entities["transfer_fee"]
        final_status = existing_status if existing_status and existing_status != "nan" else entities["status"]
        final_nat = PLAYER_NATIONALITY.get(final_player, entities["national_team"])

        categories.append(cat)
        sentiments.append(sent)
        players.append(final_player)
        national_teams.append(final_nat)
        from_clubs.append(final_from)
        to_clubs.append(final_to)
        fees.append(final_fee)
        fee_nums.append(parse_numeric_fee(final_fee))
        statuses.append(final_status)

    df["category"] = categories
    df["league"] = categories
    df["sentiment"] = sentiments
    df["player_name"] = players
    df["national_team"] = national_teams
    df["from_club"] = from_clubs
    df["to_club"] = to_clubs
    df["transfer_fee"] = fees
    df["fee_numeric"] = fee_nums
    df["status"] = statuses

    return df
