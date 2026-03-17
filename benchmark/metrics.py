"""Precision@k, MRR, and hit rate calculations."""


def precision_at_k(ranked: list[str], relevant: list[str], k: int) -> float:
    """Fraction of top-k results that are relevant."""
    top_k = ranked[:k]
    relevant_set = set(relevant)
    hits = sum(1 for t in top_k if t in relevant_set)
    return hits / k


def reciprocal_rank(ranked: list[str], relevant: list[str]) -> float:
    """1 / position of first relevant result (0 if none found)."""
    relevant_set = set(relevant)
    for i, tool in enumerate(ranked):
        if tool in relevant_set:
            return 1.0 / (i + 1)
    return 0.0


def hit_rate(ranked: list[str], relevant: list[str], k: int) -> float:
    """1 if any relevant tool appears in top-k, else 0."""
    top_k = set(ranked[:k])
    return 1.0 if top_k & set(relevant) else 0.0


def compute_metrics(
    ranked: list[str], relevant: list[str]
) -> dict[str, float]:
    """Compute all metrics for a single query result."""
    return {
        "mrr": reciprocal_rank(ranked, relevant),
        "p@1": precision_at_k(ranked, relevant, 1),
        "p@3": precision_at_k(ranked, relevant, 3),
        "p@5": precision_at_k(ranked, relevant, 5),
        "hit@5": hit_rate(ranked, relevant, 5),
    }
