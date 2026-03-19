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

    def suggest_tools(
        self, query: str, excluded: set[str] | None = None,
    ) -> SuggestionSession:
        """Decompose query, rank tools, return session with ranked candidates.

        excluded: tools to omit (e.g. previously rejected in this session).
        """
        # 1. Decompose
        subqueries = self._decomposer.decompose(query)

        # 2. Embed subqueries
        subquery_embeddings = self._embedder.embed_batch(subqueries)

        # 3. Semantic rank (omit excluded tools)
        sem_scores = semantic_rank(
            subquery_embeddings, self._tools_list, excluded=excluded,
        )

        # 4. Historical rank (with distance threshold, omit excluded)
        index = self._storage.load_index()
        hist_scores = historical_rank(
            subquery_embeddings, index,
            similarity_threshold=self._config.historical_similarity_threshold,
            excluded=excluded,
        )

        # 5. Fuse via interleave with holdout
        if hist_scores:
            top_k = fuse_rankings(
                sem_scores, hist_scores,
                top_k=self._config.top_k,
                min_semantic_slots=self._config.min_semantic_slots,
                min_historical_slots=self._config.min_historical_slots,
            )
        else:
            # No history yet — pure semantic, take top-k
            ranked = sorted(sem_scores.items(), key=lambda x: x[1], reverse=True)
            top_k = ranked[: self._config.top_k]

        # 6. Epsilon-greedy exploration
        if random.random() < self._config.epsilon:
            top_names = {name for name, _ in top_k}
            all_excluded = (excluded or set()) | top_names
            candidates = [t for t in self._tools if t not in all_excluded]
            if candidates and top_k:
                random_tool = random.choice(candidates)
                # Replace last slot
                top_k[-1] = (random_tool, 0.0)

        # 7. Append __none__ sentinel
        top_k.append((NONE_SENTINEL, 0.0))

        session = SuggestionSession(
            query=query,
            subqueries=subqueries,
            subquery_embeddings=subquery_embeddings,
            ranked_tools=top_k,
            session_id=uuid.uuid4().hex[:12],
        )
        return session

    def continue_session(self, session: SuggestionSession) -> SuggestionSession:
        """Continue a session after NONE was selected.

        Re-runs suggest_tools with all previously seen tools excluded.
        """
        previously_seen = {
            name for name, _ in session.ranked_tools if name != NONE_SENTINEL
        }
        return self.suggest_tools(session.query, excluded=previously_seen)

    def review_tools(
        self, session: SuggestionSession, reviews: list[ToolReview]
    ) -> None:
        """Record agent feedback for suggested tools.

        If NONE_SENTINEL is in the reviews, all presented tools not otherwise
        reviewed are automatically logged as 'unrelated'.
        """
        multipliers = self._config.fitness_multipliers

        # Check if NONE was selected
        reviewed_names = set()
        none_selected = False
        for review in reviews:
            if review.tool_name == NONE_SENTINEL:
                none_selected = True
            else:
                reviewed_names.add(review.tool_name)

        # If NONE selected, build implicit unrelated reviews for all
        # presented tools that weren't explicitly reviewed
        effective_reviews = list(reviews)
        if none_selected:
            presented = {
                name for name, _ in session.ranked_tools
                if name != NONE_SENTINEL
            }
            for tool_name in presented - reviewed_names:
                effective_reviews.append(
                    ToolReview(tool_name=tool_name, rating="unrelated")
                )

        # Store one review entry per subquery embedding (not the mean)
        for review in effective_reviews:
            if review.tool_name == NONE_SENTINEL:
                continue
            fitness = multipliers.get(review.rating, 1.0)
            for sq_emb in session.subquery_embeddings:
                entry = ReviewEntry(
                    tool_name=review.tool_name,
                    query_embedding=sq_emb.astype(np.float32),
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
