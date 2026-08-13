"""
MercatoPULSE — Tests Déduplication Sémantique (pytest)
======================================================
Teste la logique de génération et comparaison des hashes sémantiques.
"""

import pytest
from src.deduplicator import SemanticDeduplicator, compute_semantic_hash


# ──────────────────────────────────────────────────────────────────────
# Tests — Semantic Hash
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestSemanticHash:
    """Tests de génération de hashes sémantiques pour la déduplication."""

    def test_same_transfer_same_hash(self):
        """Deux articles sur le même transfert → même hash."""
        h1 = compute_semantic_hash(player="Mbappé", from_club="PSG", to_club="Real Madrid")
        h2 = compute_semantic_hash(player="mbappé", from_club="psg", to_club="real madrid")
        assert h1 == h2

    def test_different_transfer_different_hash(self):
        """Deux transferts différents → hashes différents."""
        h1 = compute_semantic_hash(player="Mbappé", from_club="PSG", to_club="Real Madrid")
        h2 = compute_semantic_hash(player="Neymar", from_club="PSG", to_club="Al-Hilal")
        assert h1 != h2

    def test_hash_is_string(self):
        """Le hash retourné est toujours une chaîne."""
        h = compute_semantic_hash(player="Salah", from_club="Liverpool", to_club=None)
        assert isinstance(h, str)
        assert len(h) > 0

    def test_hash_with_none_clubs(self):
        """Un hash avec clubs manquants ne doit pas lever d'exception."""
        h = compute_semantic_hash(player="Bellingham", from_club=None, to_club=None)
        assert isinstance(h, str)

    def test_hash_normalizes_accents(self):
        """Les accents sont normalisés (Mbappé == Mbappe)."""
        h1 = compute_semantic_hash(player="Mbappé", from_club="PSG", to_club="Real")
        h2 = compute_semantic_hash(player="Mbappe", from_club="PSG", to_club="Real")
        # Après normalisation, les hashes doivent correspondre
        assert h1 == h2


# ──────────────────────────────────────────────────────────────────────
# Tests — Déduplicateur
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestDeduplicator:
    """Tests du moteur de déduplication d'articles."""

    def _make_article(self, player, from_club, to_club, summary="", credibility=4.0):
        return {
            "player_name": player,
            "from_club": from_club,
            "to_club": to_club,
            "summary": summary,
            "credibility_score": credibility,
            "title": f"{player} transfer to {to_club}",
        }

    def test_dedup_removes_duplicate(self):
        """Deux articles identiques → un seul conservé."""
        articles = [
            self._make_article("Mbappé", "PSG", "Real Madrid"),
            self._make_article("Mbappé", "PSG", "Real Madrid"),
        ]
        dedup = SemanticDeduplicator()
        result = dedup.deduplicate(articles)
        assert len(result) == 1

    def test_dedup_keeps_different_articles(self):
        """Deux articles sur des transferts différents → tous les deux conservés."""
        articles = [
            self._make_article("Mbappé", "PSG", "Real Madrid"),
            self._make_article("Neymar", "PSG", "Al-Hilal"),
        ]
        dedup = SemanticDeduplicator()
        result = dedup.deduplicate(articles)
        assert len(result) == 2

    def test_dedup_keeps_highest_credibility(self):
        """En cas de doublon, l'article avec la meilleure crédibilité est conservé."""
        articles = [
            self._make_article("Mbappé", "PSG", "Real Madrid", credibility=3.0),
            self._make_article("Mbappé", "PSG", "Real Madrid", credibility=4.8),
        ]
        dedup = SemanticDeduplicator()
        result = dedup.deduplicate(articles)
        assert len(result) == 1
        assert result[0]["credibility_score"] == 4.8

    def test_dedup_empty_list(self):
        """Une liste vide retourne une liste vide."""
        dedup = SemanticDeduplicator()
        result = dedup.deduplicate([])
        assert result == []

    def test_dedup_single_article(self):
        """Un seul article n'est jamais supprimé."""
        articles = [self._make_article("Salah", "Liverpool", "Saudi")]
        dedup = SemanticDeduplicator()
        result = dedup.deduplicate(articles)
        assert len(result) == 1
