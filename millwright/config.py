"""Configuration dataclass with all Millwright hyperparameters."""

from dataclasses import dataclass, field


@dataclass
class MillwrightConfig:
    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # Ranking fusion (interleave with holdout)
    top_k: int = 5
    min_semantic_slots: int = 2
    min_historical_slots: int = 1

    # Historical lookup
    historical_similarity_threshold: float = 0.3

    # Exploration
    epsilon: float = 0.1

    # Fitness multipliers
    fitness_perfect: float = 1.4
    fitness_related: float = 1.05
    fitness_unrelated: float = 0.75
    fitness_broken: float = 0.35

    # Compaction
    max_clusters_per_tool: int = 10
    min_reviews_for_compaction: int = 3

    # Storage
    storage_dir: str = "./millwright_data"

    @property
    def fitness_multipliers(self) -> dict[str, float]:
        return {
            "perfect": self.fitness_perfect,
            "related": self.fitness_related,
            "unrelated": self.fitness_unrelated,
            "broken": self.fitness_broken,
        }
