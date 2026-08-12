#!/usr/bin/env python3
"""
deduplicator.py — MercatoPULSE V2 Déduplication Sémantique

Fusionne les articles qui parlent du même transfert (même joueur, mêmes clubs)
provenant de sources différentes. Garde l'article le plus complet et enrichit
avec les informations des doublons.
"""
from __future__ import annotations

import logging
import re
import unicodedata
from typing import Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def normalize_hash(s: str) -> str:
    """Normalise une chaîne pour comparaison de hash."""
    s = unicodedata.normalize("NFD", s.lower().strip())
    s = re.sub(r"[\u0300-\u036f]", "", s)
    s = re.sub(r"[^a-z0-9]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def compute_article_quality_score(row: Dict) -> float:
    """
    Calcule un score de qualité pour un article.
    Plus le score est élevé, plus l'article est complet.
    """
    score = 0.0

    # Joueur identifié
    player = str(row.get("player_name", "")).strip()
    if player and player not in ["", "Joueur Mercato", "Joueur Star", "nan"]:
        score += 3.0

    # Clubs identifiés
    from_c = str(row.get("from_club", "")).strip()
    to_c = str(row.get("to_club", "")).strip()
    if from_c and from_c not in ["", "Club Vendeur", "nan"]:
        score += 2.0
    if to_c and to_c not in ["", "Club Acheteur", "nan"]:
        score += 2.0

    # Montant identifié
    fee = str(row.get("transfer_fee", "")).strip()
    if fee and fee not in ["", "Non communiqué", "nan"]:
        score += 2.0

    fee_num = float(row.get("fee_numeric", 0) or 0)
    if fee_num > 0:
        score += 1.0

    # Image disponible
    img = str(row.get("image_url", "")).strip()
    if img and img.startswith("http"):
        score += 1.5

    # Crédibilité source
    cred = float(row.get("credibility", 0) or 0)
    score += cred

    # Statut avancé (OFFICIEL ou HERE WE GO vaut plus)
    status = str(row.get("status", "")).upper()
    if "OFFICIEL" in status:
        score += 2.0
    elif "HERE WE GO" in status:
        score += 1.5
    elif "NEGOCIATION" in status:
        score += 0.5

    # Longueur du résumé (plus c'est détaillé, mieux c'est)
    summary_len = len(str(row.get("summary", "")))
    score += min(summary_len / 200, 2.0)

    return score


def merge_articles(primary: Dict, secondary: Dict) -> Dict:
    """
    Fusionne deux articles en enrichissant le primary avec les infos du secondary.
    Le primary est l'article de meilleure qualité.
    """
    result = dict(primary)

    # Enrichir les champs vides du primary avec ceux du secondary
    enrichable_fields = [
        "player_name", "from_club", "to_club", "transfer_fee",
        "national_team", "image_url", "league",
    ]
    placeholder_values = {
        "player_name": ["", "Joueur Mercato", "Joueur Star", "nan", "None"],
        "from_club": ["", "Club Vendeur", "Club Acquéreur", "nan", "None"],
        "to_club": ["", "Club Acheteur", "Club Cible", "nan", "None"],
        "transfer_fee": ["", "Non communiqué", "nan", "None"],
        "national_team": ["", "nan", "None"],
        "image_url": ["", "nan", "None"],
        "league": ["", "nan", "None"],
    }

    for field in enrichable_fields:
        primary_val = str(result.get(field, "")).strip()
        secondary_val = str(secondary.get(field, "")).strip()
        bad_vals = placeholder_values.get(field, ["", "nan", "None"])

        if primary_val in bad_vals and secondary_val not in bad_vals:
            result[field] = secondary_val

    # Prendre le fee_numeric le plus élevé (plus précis)
    p_fee = float(result.get("fee_numeric", 0) or 0)
    s_fee = float(secondary.get("fee_numeric", 0) or 0)
    if s_fee > p_fee:
        result["fee_numeric"] = s_fee

    # Prendre la crédibilité la plus haute
    p_cred = float(result.get("credibility", 0) or 0)
    s_cred = float(secondary.get("credibility", 0) or 0)
    if s_cred > p_cred:
        result["credibility"] = s_cred

    # Prendre le statut le plus avancé
    status_priority = {"OFFICIEL ✅": 4, "HERE WE GO 🔥": 3, "NEGOCIATION 💬": 2, "RUMEUR 📰": 1}
    p_prio = status_priority.get(str(result.get("status", "")), 0)
    s_prio = status_priority.get(str(secondary.get("status", "")), 0)
    if s_prio > p_prio:
        result["status"] = secondary.get("status")

    # Prendre l'image du secondary si le primary n'en a pas
    p_img = str(result.get("image_url", "")).strip()
    s_img = str(secondary.get("image_url", "")).strip()
    if (not p_img or not p_img.startswith("http")) and s_img.startswith("http"):
        result["image_url"] = s_img

    return result


def deduplicate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Déduplique un DataFrame d'articles par semantic_hash.
    Garde l'article le plus complet et fusionne les infos des doublons.
    """
    if df.empty or "semantic_hash" not in df.columns:
        return df

    # Filtrer les articles sans hash valide
    df["_hash_clean"] = df["semantic_hash"].apply(
        lambda h: normalize_hash(str(h)) if pd.notna(h) and str(h).strip() not in ["", "nan", "unknown__unknown__unknown"] else ""
    )

    # Séparer les articles avec et sans hash
    has_hash = df[df["_hash_clean"] != ""].copy()
    no_hash = df[df["_hash_clean"] == ""].copy()

    if has_hash.empty:
        df.drop(columns=["_hash_clean"], inplace=True, errors="ignore")
        return df

    # Calculer le score de qualité
    has_hash["_quality"] = has_hash.apply(
        lambda row: compute_article_quality_score(row.to_dict()), axis=1
    )

    # Grouper par hash et fusionner
    deduped_rows = []
    groups = has_hash.groupby("_hash_clean")

    for hash_key, group in groups:
        # Trier par qualité décroissante
        sorted_group = group.sort_values("_quality", ascending=False)
        rows = sorted_group.to_dict("records")

        # Garder le meilleur, enrichir avec les autres
        best = rows[0]
        for other in rows[1:]:
            best = merge_articles(best, other)

        deduped_rows.append(best)

    deduped_df = pd.DataFrame(deduped_rows)

    # Rejoindre avec les articles sans hash
    result = pd.concat([deduped_df, no_hash], ignore_index=True)

    # Nettoyage des colonnes temporaires
    result.drop(columns=["_hash_clean", "_quality"], inplace=True, errors="ignore")

    duplicates_removed = len(has_hash) - len(deduped_df)
    if duplicates_removed > 0:
        logger.info("🔄 Déduplication: %d doublons fusionnés (%d → %d articles uniques)",
                     duplicates_removed, len(df), len(result))

    return result.reset_index(drop=True)
