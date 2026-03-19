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
    excluded: set[str] | None = None,
) -> dict[str, float]:
    """Rank tools by max cosine similarity across subquery embeddings.

    Omits tools in the excluded set (e.g. previously rejected in this session).
    """
    scores: dict[str, float] = {}
    for tool in tools:
        if tool.embedding is None:
            continue
        if excluded and tool.name in excluded:
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
    similarity_threshold: float = 0.0,
    excluded: set[str] | None = None,
) -> dict[str, float]:
    """Rank tools by historical fitness weighted by embedding similarity.

    Only considers index entries with similarity >= similarity_threshold.
    Omits tools in the excluded set.
    """
    if not index:
        return {}

    scores: dict[str, float] = {}
    weights: dict[str, float] = {}

    for entry in index:
        if excluded and entry.tool_name in excluded:
            continue
        max_sim = max(
            cosine_similarity(sq_emb, entry.query_centroid)
            for sq_emb in subquery_embeddings
        )
        if max_sim < similarity_threshold:
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
    top_k: int,
    min_semantic_slots: int = 2,
    min_historical_slots: int = 1,
) -> list[tuple[str, float]]:
    """Fuse semantic and historical rankings via holdout + score-based rerank.

    Phase 1 (candidate selection): Build a candidate pool of top_k tools,
    guaranteeing at least min_semantic_slots from semantic ranking and
    min_historical_slots from historical ranking. Remaining slots filled
    by interleaving both lists.

    Phase 2 (rerank): Score each candidate using normalized scores from
    both signals and sort by combined score. This lets historical learning
    actually promote tools to #1 while the holdout ensures signal diversity.

    Returns a sorted list of (tool_name, fused_score) tuples.
    """
    # Sort each signal independently
    sem_ranked = sorted(semantic_scores.items(), key=lambda x: x[1], reverse=True)
    hist_ranked = sorted(historical_scores.items(), key=lambda x: x[1], reverse=True)

    # Phase 1: Build candidate pool with holdout guarantees
    candidates: set[str] = set()

    sem_idx = 0
    for _ in range(min_semantic_slots):
        while sem_idx < len(sem_ranked) and sem_ranked[sem_idx][0] in candidates:
            sem_idx += 1
        if sem_idx < len(sem_ranked):
            candidates.add(sem_ranked[sem_idx][0])
            sem_idx += 1

    hist_idx = 0
    for _ in range(min_historical_slots):
        while hist_idx < len(hist_ranked) and hist_ranked[hist_idx][0] in candidates:
            hist_idx += 1
        if hist_idx < len(hist_ranked):
            candidates.add(hist_ranked[hist_idx][0])
            hist_idx += 1

    # Fill remaining slots by interleaving
    while len(candidates) < top_k:
        added = False
        while sem_idx < len(sem_ranked) and sem_ranked[sem_idx][0] in candidates:
            sem_idx += 1
        if sem_idx < len(sem_ranked) and len(candidates) < top_k:
            candidates.add(sem_ranked[sem_idx][0])
            sem_idx += 1
            added = True

        while hist_idx < len(hist_ranked) and hist_ranked[hist_idx][0] in candidates:
            hist_idx += 1
        if hist_idx < len(hist_ranked) and len(candidates) < top_k:
            candidates.add(hist_ranked[hist_idx][0])
            hist_idx += 1
            added = True

        if not added:
            break

    # Phase 2: Score and rank candidates using both signals
    norm_sem = _normalize_scores(semantic_scores)
    norm_hist = _normalize_scores(historical_scores)

    scored = []
    for name in candidates:
        s = norm_sem.get(name, 0.0)
        h = norm_hist.get(name, 0.0)
        # Equal weight to both signals for the final ordering
        fused_score = s + h
        scored.append((name, fused_score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
