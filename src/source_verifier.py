"""
source_verifier.py — Évaluation et vérification de crédibilité des sources Mercato & Football
MercatoPulse — Supporte les sources sportives & mercato (Sky Sports, L'Équipe, Marca, Fabrizio Romano, Foot Mercato, etc.)
"""

import pandas as pd
import os

# ─────────────────────────────────────────────
# BARÈME DE CRÉDIBILITÉ MERCATO (1-5 ÉTOILES)
# Basé sur la Tier List internationale des journalistes & médias foot
# ─────────────────────────────────────────────
MERCATO_TRUSTED_SOURCES = {
    # ── Tier 1 / 5 Étoiles — Sources Officielles & Agences Réputées ──
    "Fabrizio Romano":             5,
    "Sky Sports Transfer Centre": 5,
    "BBC Sport Football":         5,
    "L'Équipe Mercato":            5,
    "David Ornstein":              5,

    # ── Tier 2 / 4 Étoiles — Médias Majeurs ──
    "Foot Mercato":               4,
    "Marca Fichajes":              4,
    "RMC Sport Mercato":           4,
    "Goal.com Mercato":            4,
    "Marca Real Madrid":           4,
    "Marca Barcelona":             4,
    "Gazzetta dello Sport Mercato": 4,
    "Transfermarkt News":          4,
    "Football Italia":             4,

    # ── Tier 3 / 3 Étoiles — Presse Spécialisée & Rumeurs ──
    "Sport.es Mercato":            3,
    "TalkSport Football":          3,
    "Eurosport Mercato":           3,
    "Saudi Pro League News":       4,
}

DEFAULT_SCORE = 3


def get_credibility(source_name: str) -> int:
    """Retourne le score de crédibilité d'une source Mercato (1 à 5)."""
    if not source_name:
        return DEFAULT_SCORE

    for key, score in MERCATO_TRUSTED_SOURCES.items():
        if key.lower() in source_name.lower() or source_name.lower() in key.lower():
            return score

    return DEFAULT_SCORE


def calculate_source_credibility(source_name: str) -> float:
    return float(get_credibility(source_name))


def verify_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les colonnes de crédibilité au DataFrame."""
    if df.empty:
        return df

    credibility_list = []

    for _, row in df.iterrows():
        src = str(row.get("source", ""))
        score = get_credibility(src)
        credibility_list.append(score)

    df["credibility"] = credibility_list
    return df
