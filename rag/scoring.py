import math


def normalize_relevance_score(score: float) -> float:
    """
    Normalize a raw Qdrant cosine similarity score to a [0.0, 1.0] relevance score.

    Qdrant returns cosine similarity scores that range from -1 to 1.
    However, in practice with well-formed embeddings, scores typically
    fall in the range [0.5, 1.0] for relevant results.

    Strategy: Apply a sigmoid-like transformation that maps the practical
    range to [0.0, 1.0], giving higher discrimination near the threshold.

    The formula: normalized = (score - offset) / (1 - offset)
    where offset is a baseline below which scores are considered noise.
    """
    offset = 0.3
    if score <= offset:
        return 0.0
    normalized = (score - offset) / (1.0 - offset)
    return min(max(normalized, 0.0), 1.0)


def is_above_threshold(score: float, threshold: float) -> bool:
    return score >= threshold


def get_relevance_label(score: float) -> str:
    if score >= 0.9:
        return "highly_relevant"
    elif score >= 0.7:
        return "relevant"
    elif score >= 0.5:
        return "partially_relevant"
    else:
        return "not_relevant"
