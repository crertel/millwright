"""Main orchestrator: suggest_tools + review_tools."""

import random
import uuid

import numpy as np

from .compaction import compact_reviews
from .config import MillwrightConfig
from .decomposer import Decomposer
from .embedder import Embedder
from .models import (
    ReviewEntry,
    SuggestionSession,
    ToolDefinition,
    ToolReview,
)
from .ranking import fuse_rankings, historical_rank, semantic_rank
from .storage import Storage


NONE_SENTINEL = "__none__"


class Toolshed:
    def __init__(
        self,
        tools: list[ToolDefinition],
        decomposer: Decomposer,
        config: MillwrightConfig | None = None,
        embedder: Embedder | None = None,
        storage: Storage | None = None,
    ):
        self._config = config or MillwrightConfig()
        self._decomposer = decomposer
        self._embedder = embedder or Embedder(self._config)
        self._storage = storage or Storage(self._config)
        self._tools = {t.name: t for t in tools}
        self._tools_list = tools

        # Pre-compute tool embeddings
        for tool in self._tools_list:
            if tool.embedding is None:
                tool.embedding = self._embedder.embed(tool.description)

    def suggest_tools(self, query: str) -> SuggestionSession:
        """Decompose query, rank tools, return session with ranked candidates."""
        # 1. Decompose
        subqueries = self._decomposer.decompose(query)

        # 2. Embed subqueries
        subquery_embeddings = self._embedder.embed_batch(subqueries)

        # 3. Semantic rank
        sem_scores = semantic_rank(subquery_embeddings, self._tools_list)

        # 4. Historical rank
        index = self._storage.load_index()
        hist_scores = historical_rank(subquery_embeddings, index)

        # 5. Fuse
        if hist_scores:
            fused = fuse_rankings(
                sem_scores, hist_scores,
                self._config.semantic_weight,
                self._config.historical_weight,
            )
        else:
            # No history yet — pure semantic
            fused = sem_scores

        # 6. Sort and take top-k
        ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)
        top_k = ranked[: self._config.top_k]

        # 7. Epsilon-greedy exploration
        if random.random() < self._config.epsilon:
            # Pick a random tool not already in top-k
            top_names = {name for name, _ in top_k}
            candidates = [t for t in self._tools if t not in top_names]
            if candidates:
                random_tool = random.choice(candidates)
                # Replace last slot
                top_k[-1] = (random_tool, 0.0)

        # 8. Append __none__ sentinel
        top_k.append((NONE_SENTINEL, 0.0))

        session = SuggestionSession(
            query=query,
            subqueries=subqueries,
            subquery_embeddings=subquery_embeddings,
            ranked_tools=top_k,
            session_id=uuid.uuid4().hex[:12],
        )
        return session

    def review_tools(
        self, session: SuggestionSession, reviews: list[ToolReview]
    ) -> None:
        """Record agent feedback for suggested tools."""
        multipliers = self._config.fitness_multipliers

        # Use mean of subquery embeddings as the query embedding
        query_emb = np.mean(session.subquery_embeddings, axis=0)
        query_emb = query_emb / (np.linalg.norm(query_emb) + 1e-10)

        for review in reviews:
            if review.tool_name == NONE_SENTINEL:
                continue
            fitness = multipliers.get(review.rating, 1.0)
            entry = ReviewEntry(
                tool_name=review.tool_name,
                query_embedding=query_emb.astype(np.float32),
                fitness=fitness,
            )
            self._storage.append_review(entry)

    def compact(self) -> None:
        """Run compaction: rebuild review index from review log."""
        reviews = self._storage.load_reviews()
        if not reviews:
            return
        index = compact_reviews(reviews, self._config)
        self._storage.save_index(index)

    def clear_data(self) -> None:
        """Clear all stored review data."""
        self._storage.clear()
