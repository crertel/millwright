"""Sentence-transformers wrapper with caching and normalization."""

import numpy as np
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer

from .config import MillwrightConfig


class Embedder:
    def __init__(self, config: MillwrightConfig):
        self._model = SentenceTransformer(config.embedding_model)
        self._cache: dict[str, NDArray[np.float32]] = {}
        self._dim = config.embedding_dim

    def embed(self, text: str) -> NDArray[np.float32]:
        if text in self._cache:
            return self._cache[text]
        vec = self._model.encode(text, normalize_embeddings=True)
        vec = np.array(vec, dtype=np.float32)
        self._cache[text] = vec
        return vec

    def embed_batch(self, texts: list[str]) -> list[NDArray[np.float32]]:
        uncached = [t for t in texts if t not in self._cache]
        if uncached:
            vecs = self._model.encode(uncached, normalize_embeddings=True)
            for t, v in zip(uncached, vecs):
                self._cache[t] = np.array(v, dtype=np.float32)
        return [self._cache[t] for t in texts]

    @property
    def dim(self) -> int:
        return self._dim
