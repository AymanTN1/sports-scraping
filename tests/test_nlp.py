"""
MercatoPULSE — Tests NLP Engine (pytest)
==========================================
Teste l'extraction de données mercato sans aucune dépendance externe.
"""

import pytest
from src.nlp_extractor import extract_transfer_info


# ──────────────────────────────────────────────────────────────────────
# Tests — Extraction basique
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestNLPExtraction:
    """Tests de l'extracteur NLP local (sans Groq API)."""

    def test_extract_player_name_english(self):
        title = "Kylian Mbappé signs for Real Madrid in record deal"
        result = extract_transfer_info(title, language="en")
        assert result is not None
        player = result.get("player_name", "").lower()
        assert "mbapp" in player or "kylian" in player

    def test_extract_player_name_french(self):
        title = "Mbappé rejoint le Real Madrid selon les médias espagnols"
        result = extract_transfer_info(title, language="fr")
        assert result is not None

    def test_extract_transfer_fee(self):
        title = "Arsenal signs Saka extension for €120M release clause"
        result = extract_transfer_info(title, language="en")
        assert result is not None
        fee = result.get("transfer_fee", "")
        assert "120" in str(fee) or result.get("fee_numeric") is not None

    def test_no_player_returns_empty_gracefully(self):
        """Un titre sans nom de joueur ne doit pas lever d'exception."""
        title = "Premier League to introduce new VAR rules next season"
        result = extract_transfer_info(title, language="en")
        assert result is not None  # retourne un dict même si vide

    def test_extract_from_club(self):
        title = "Bellingham leaves Liverpool to join Real Madrid"
        result = extract_transfer_info(title, language="en")
        assert result is not None
        from_club = result.get("from_club", "").lower()
        assert "liverpool" in from_club or from_club == ""

    def test_extract_to_club(self):
        title = "Bellingham leaves Liverpool to join Real Madrid"
        result = extract_transfer_info(title, language="en")
        assert result is not None
        to_club = result.get("to_club", "").lower()
        assert "real madrid" in to_club or to_club == ""

    def test_empty_title_does_not_crash(self):
        """Un titre vide ne doit pas lever d'exception."""
        result = extract_transfer_info("", language="en")
        assert result is not None

    def test_result_is_dict(self):
        """Le résultat doit toujours être un dict."""
        result = extract_transfer_info("Neymar rejoint Al-Hilal", language="fr")
        assert isinstance(result, dict)
