"""Core data structures for Millwright."""

from dataclasses import dataclass, field
import numpy as np
from numpy.typing import NDArray


@dataclass
class ToolDefinition:
    name: str
    description: str
    category: str
    embedding: NDArray[np.float32] | None = field(default=None, repr=False)


@dataclass
class SuggestionSession:
    query: str
    subqueries: list[str]
    subquery_embeddings: list[NDArray[np.float32]]
    ranked_tools: list[tuple[str, float]]  # (tool_name, score)
    session_id: str = ""


@dataclass
class ReviewEntry:
    tool_name: str
    query_embedding: NDArray[np.float32]
    fitness: float


@dataclass
class ReviewIndexEntry:
    tool_name: str
    query_centroid: NDArray[np.float32]
    aggregate_fitness: float
    count: int


@dataclass
class ToolReview:
    tool_name: str
    rating: str  # "perfect", "related", "unrelated", "broken"
