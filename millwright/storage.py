"""File-based storage: JSONL review log + JSON review index."""

import json
import os
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from .config import MillwrightConfig
from .models import ReviewEntry, ReviewIndexEntry


class Storage:
    def __init__(self, config: MillwrightConfig):
        self._dir = Path(config.storage_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._log_path = self._dir / "review_log.jsonl"
        self._index_path = self._dir / "review_index.json"

    def append_review(self, entry: ReviewEntry) -> None:
        record = {
            "tool_name": entry.tool_name,
            "query_embedding": entry.query_embedding.tolist(),
            "fitness": entry.fitness,
        }
        with open(self._log_path, "a") as f:
            f.write(json.dumps(record) + "\n")

    def load_reviews(self) -> list[ReviewEntry]:
        if not self._log_path.exists():
            return []
        entries = []
        with open(self._log_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                entries.append(ReviewEntry(
                    tool_name=record["tool_name"],
                    query_embedding=np.array(record["query_embedding"], dtype=np.float32),
                    fitness=record["fitness"],
                ))
        return entries

    def save_index(self, entries: list[ReviewIndexEntry]) -> None:
        records = []
        for e in entries:
            records.append({
                "tool_name": e.tool_name,
                "query_centroid": e.query_centroid.tolist(),
                "aggregate_fitness": e.aggregate_fitness,
                "count": e.count,
            })
        with open(self._index_path, "w") as f:
            json.dump(records, f)

    def load_index(self) -> list[ReviewIndexEntry]:
        if not self._index_path.exists():
            return []
        with open(self._index_path) as f:
            records = json.load(f)
        return [
            ReviewIndexEntry(
                tool_name=r["tool_name"],
                query_centroid=np.array(r["query_centroid"], dtype=np.float32),
                aggregate_fitness=r["aggregate_fitness"],
                count=r["count"],
            )
            for r in records
        ]

    def clear(self) -> None:
        if self._log_path.exists():
            self._log_path.unlink()
        if self._index_path.exists():
            self._index_path.unlink()
