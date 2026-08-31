import pytest
from rag.scoring import normalize_relevance_score, is_above_threshold, get_relevance_label


class TestNormalizeRelevanceScore:
    def test_high_score(self):
        score = normalize_relevance_score(0.95)
        assert score >= 0.9

    def test_medium_score(self):
        score = normalize_relevance_score(0.75)
        assert 0.5 <= score <= 1.0

    def test_low_score(self):
        score = normalize_relevance_score(0.4)
        assert score < 0.5

    def test_below_offset(self):
        score = normalize_relevance_score(0.2)
        assert score == 0.0

    def test_exact_offset(self):
        score = normalize_relevance_score(0.3)
        assert score == 0.0

    def test_perfect_score(self):
        score = normalize_relevance_score(1.0)
        assert score == 1.0

    def test_range_bounds(self):
        for raw in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
            score = normalize_relevance_score(raw)
            assert 0.0 <= score <= 1.0


class TestThreshold:
    def test_above_threshold(self):
        assert is_above_threshold(0.75, 0.70) is True

    def test_below_threshold(self):
        assert is_above_threshold(0.65, 0.70) is False

    def test_exact_threshold(self):
        assert is_above_threshold(0.70, 0.70) is True

    def test_default_threshold(self):
        from config.settings import settings
        assert is_above_threshold(0.71, settings.rag_score_threshold) is True
        assert is_above_threshold(0.69, settings.rag_score_threshold) is False


class TestRelevanceLabel:
    def test_highly_relevant(self):
        assert get_relevance_label(0.95) == "highly_relevant"

    def test_relevant(self):
        assert get_relevance_label(0.75) == "relevant"

    def test_partially_relevant(self):
        assert get_relevance_label(0.55) == "partially_relevant"

    def test_not_relevant(self):
        assert get_relevance_label(0.3) == "not_relevant"
