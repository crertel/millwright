"""Semantic ranking, historical ranking, and rank fusion."""

import numpy as np
from numpy.typing import NDArray

from .models import ToolDefinition, ReviewIndexEntry


def cosine_similarity(a: NDArray[np.float32], b: NDArray[np.float32]) -> float:
    """Cosine similarity between two normalized vectors (just dot product)."""
    return float(np.dot(a, b))


def semantic_rank(
    subquery_embeddings: list[NDArray[np.float32]],
    tools: list[ToolDefinition],
) -> dict[str, float]:
    """Rank tools by max cosine similarity across subquery embeddings."""
    scores: dict[str, float] = {}
    for tool in tools:
        if tool.embedding is None:
            continue
        max_sim = max(
            cosine_similarity(sq_emb, tool.embedding)
            for sq_emb in subquery_embeddings
        )
        scores[tool.name] = max_sim
    return scores


def historical_rank(
    subquery_embeddings: list[NDArray[np.float32]],
    index: list[ReviewIndexEntry],
) -> dict[str, float]:
    """Rank tools by historical fitness weighted by embedding similarity."""
    if not index:
        return {}

    scores: dict[str, float] = {}
    weights: dict[str, float] = {}

    for entry in index:
        max_sim = max(
            cosine_similarity(sq_emb, entry.query_centroid)
            for sq_emb in subquery_embeddings
        )
        # Only consider entries with positive similarity
        if max_sim <= 0:
            continue

        weight = max_sim * entry.count
        weighted_fitness = entry.aggregate_fitness * weight

        if entry.tool_name not in scores:
            scores[entry.tool_name] = 0.0
            weights[entry.tool_name] = 0.0
        scores[entry.tool_name] += weighted_fitness
        weights[entry.tool_name] += weight

    # Normalize by total weight
    for name in scores:
        if weights[name] > 0:
            scores[name] = scores[name] / weights[name]

    return scores


def _normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    """Normalize scores to [0, 1] range."""
    if not scores:
        return {}
    vals = list(scores.values())
    min_v, max_v = min(vals), max(vals)
    span = max_v - min_v
    if span == 0:
        return {k: 1.0 for k in scores}
    return {k: (v - min_v) / span for k, v in scores.items()}


def fuse_rankings(
    semantic_scores: dict[str, float],
    historical_scores: dict[str, float],
    semantic_weight: float,
    historical_weight: float,
) -> dict[str, float]:
    """Fuse semantic and historical rankings via weighted sum of normalized scores."""
    norm_sem = _normalize_scores(semantic_scores)
    norm_hist = _normalize_scores(historical_scores)

    all_tools = set(norm_sem) | set(norm_hist)
    fused: dict[str, float] = {}
    for name in all_tools:
        s = norm_sem.get(name, 0.0)
        h = norm_hist.get(name, 0.0)
        fused[name] = semantic_weight * s + historical_weight * h

    return fused
