"""K-means compaction of review logs into review index entries."""

from collections import defaultdict

import numpy as np
from sklearn.cluster import KMeans

from .config import MillwrightConfig
from .models import ReviewEntry, ReviewIndexEntry


def compact_reviews(
    reviews: list[ReviewEntry],
    config: MillwrightConfig,
) -> list[ReviewIndexEntry]:
    """Group reviews by tool, K-means cluster their query embeddings,
    output one index entry per centroid with fitness weighted by
    similarity to centroid."""
    # Group by tool
    by_tool: dict[str, list[ReviewEntry]] = defaultdict(list)
    for r in reviews:
        by_tool[r.tool_name].append(r)

    index_entries: list[ReviewIndexEntry] = []

    for tool_name, tool_reviews in by_tool.items():
        n = len(tool_reviews)
        if n < config.min_reviews_for_compaction:
            # Too few reviews — emit one entry with simple average
            embeddings = np.array([r.query_embedding for r in tool_reviews])
            centroid = embeddings.mean(axis=0)
            centroid = centroid / (np.linalg.norm(centroid) + 1e-10)
            avg_fitness = sum(r.fitness for r in tool_reviews) / n
            index_entries.append(ReviewIndexEntry(
                tool_name=tool_name,
                query_centroid=centroid.astype(np.float32),
                aggregate_fitness=avg_fitness,
                count=n,
            ))
            continue

        # K-means clustering
        n_clusters = min(config.max_clusters_per_tool, n)
        embeddings = np.array([r.query_embedding for r in tool_reviews])
        fitnesses = np.array([r.fitness for r in tool_reviews])

        kmeans = KMeans(n_clusters=n_clusters, n_init="auto", random_state=42)
        labels = kmeans.fit_predict(embeddings)

        for cluster_id in range(n_clusters):
            mask = labels == cluster_id
            if not mask.any():
                continue
            cluster_embeddings = embeddings[mask]
            cluster_fitnesses = fitnesses[mask]
            count = int(mask.sum())

            centroid = cluster_embeddings.mean(axis=0)
            centroid = centroid / (np.linalg.norm(centroid) + 1e-10)

            # Weight each review's fitness by its cosine similarity to the
            # cluster centroid, so reviews near the center count more.
            similarities = cluster_embeddings @ centroid
            similarities = np.clip(similarities, 0.0, None)
            sim_sum = similarities.sum()
            if sim_sum > 0:
                weighted_fitness = float((cluster_fitnesses * similarities).sum() / sim_sum)
            else:
                weighted_fitness = float(cluster_fitnesses.mean())

            index_entries.append(ReviewIndexEntry(
                tool_name=tool_name,
                query_centroid=centroid.astype(np.float32),
                aggregate_fitness=weighted_fitness,
                count=count,
            ))

    return index_entries
