"""Baseline rankers: random and TF-IDF."""

import random

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from millwright.models import ToolDefinition


def random_rank(
    tools: list[ToolDefinition], excluded: set[str] | None = None
) -> dict[str, float]:
    """Uniform random scores for all tools."""
    excluded = excluded or set()
    return {
        t.name: random.random()
        for t in tools
        if t.name not in excluded
    }


def tfidf_rank(
    query: str,
    tools: list[ToolDefinition],
    excluded: set[str] | None = None,
) -> dict[str, float]:
    """TF-IDF cosine similarity between query and tool descriptions."""
    excluded = excluded or set()
    eligible = [t for t in tools if t.name not in excluded]
    if not eligible:
        return {}

    corpus = [t.description for t in eligible]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus + [query])

    query_vec = tfidf_matrix[-1]
    tool_vecs = tfidf_matrix[:-1]
    sims = cosine_similarity(query_vec, tool_vecs).flatten()

    return {t.name: float(sims[i]) for i, t in enumerate(eligible)}
