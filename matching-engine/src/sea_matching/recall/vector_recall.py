"""Vector similarity based candidate recall using dense embeddings.

Supports two backends:
- **sentence-transformers** with local FAISS index (lightweight, no external service)
- **Milvus/pgvector** for production deployments (optional)

The local FAISS approach is the default and requires no external infrastructure.
It encodes product titles into dense vectors using a multilingual sentence
transformer and finds nearest neighbours using FAISS IndexFlatIP.

Requirements (local mode):
    pip install sentence-transformers faiss-cpu

Requirements (Milvus mode):
    pip install pymilvus sentence-transformers

Configuration (in default.yaml):
    recall:
      strategies:
        - vector
      vector:
        backend: local       # local | milvus
        model_name: paraphrase-multilingual-MiniLM-L12-v2
        top_k: 30
        min_similarity: 0.4
        # Milvus settings (only when backend: milvus)
        milvus_host: localhost
        milvus_port: 19530
        collection_name: sea_matching_vectors
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from sea_matching.models.match_result import StandardizedItem

logger = logging.getLogger(__name__)


class VectorRecall:
    """Recall candidates using dense vector similarity."""

    def __init__(
        self,
        backend: str = "local",
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        top_k: int = 30,
        min_similarity: float = 0.4,
        milvus_host: str = "localhost",
        milvus_port: int = 19530,
        collection_name: str = "sea_matching_vectors",
    ):
        self.backend = backend
        self.model_name = model_name
        self.top_k = top_k
        self.min_similarity = min_similarity
        self._milvus_host = milvus_host
        self._milvus_port = milvus_port
        self._collection_name = collection_name

        self._model: Any = None
        self._index: Any = None  # FAISS index for local mode
        self._target_items: list[StandardizedItem] = []
        self._available = False

        self._init_model()

    def _init_model(self) -> None:
        """Load the sentence transformer model."""
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            self._available = True
            logger.info("Vector recall model loaded: %s", self.model_name)
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers faiss-cpu"
            )
        except Exception as exc:
            logger.warning("Failed to load vector model: %s", exc)

    @property
    def available(self) -> bool:
        return self._available

    def _encode_items(self, items: list[StandardizedItem]) -> np.ndarray:
        """Encode item titles into dense vectors.

        Combines title + brand_std for richer representations.
        """
        texts = []
        for item in items:
            parts = [item.title]
            if item.brand_std:
                parts.append(item.brand_std)
            texts.append(" ".join(parts))

        embeddings = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=64,
        )
        return np.array(embeddings, dtype=np.float32)

    def build_index(self, target_items: list[StandardizedItem]) -> None:
        """Build vector index from target items."""
        if not self._available:
            logger.warning("Vector recall unavailable — skipping index build")
            return

        self._target_items = target_items

        if self.backend == "local":
            self._build_faiss_index(target_items)
        elif self.backend == "milvus":
            self._build_milvus_index(target_items)
        else:
            logger.warning("Unknown vector backend: %s", self.backend)

    def _build_faiss_index(self, items: list[StandardizedItem]) -> None:
        """Build a FAISS inner-product (cosine) index."""
        try:
            import faiss
        except ImportError:
            logger.warning("faiss-cpu not installed. Run: pip install faiss-cpu")
            self._available = False
            return

        embeddings = self._encode_items(items)
        dim = embeddings.shape[1]

        # Use inner product (cosine similarity for normalised vectors)
        self._index = faiss.IndexFlatIP(dim)
        self._index.add(embeddings)
        logger.info(
            "Built FAISS index: %d vectors, dim=%d", len(items), dim
        )

    def _build_milvus_index(self, items: list[StandardizedItem]) -> None:
        """Index items into a Milvus collection."""
        try:
            from pymilvus import (
                Collection,
                CollectionSchema,
                DataType,
                FieldSchema,
                connections,
                utility,
            )
        except ImportError:
            logger.warning("pymilvus not installed. Run: pip install pymilvus")
            self._available = False
            return

        try:
            connections.connect(host=self._milvus_host, port=self._milvus_port)
        except Exception as exc:
            logger.warning("Milvus connection failed: %s", exc)
            self._available = False
            return

        # Drop existing collection
        if utility.has_collection(self._collection_name):
            utility.drop_collection(self._collection_name)

        # Encode items
        embeddings = self._encode_items(items)
        dim = embeddings.shape[1]

        # Create collection schema
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="item_id", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
        ]
        schema = CollectionSchema(fields, description="SEA matching item vectors")
        collection = Collection(self._collection_name, schema)

        # Insert data
        item_ids = [item.item_id for item in items]
        collection.insert([item_ids, embeddings.tolist()])

        # Create index
        index_params = {
            "metric_type": "IP",  # Inner product (cosine for normalised vectors)
            "index_type": "IVF_FLAT",
            "params": {"nlist": min(128, len(items))},
        }
        collection.create_index("embedding", index_params)
        collection.load()

        self._milvus_collection = collection
        logger.info("Built Milvus index: %d vectors in %s", len(items), self._collection_name)

    def recall(
        self, source_item: StandardizedItem
    ) -> list[tuple[StandardizedItem, float]]:
        """Find vector-similar candidates for *source_item*."""
        if not self._available:
            return []

        if self.backend == "local":
            return self._recall_faiss(source_item)
        elif self.backend == "milvus":
            return self._recall_milvus(source_item)
        return []

    def _recall_faiss(
        self, source_item: StandardizedItem
    ) -> list[tuple[StandardizedItem, float]]:
        """Search FAISS index for nearest neighbours."""
        if self._index is None:
            return []

        query_vec = self._encode_items([source_item])
        scores, indices = self._index.search(query_vec, self.top_k)

        candidates: list[tuple[StandardizedItem, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._target_items):
                continue
            sim = float(score)  # Already cosine similarity for normalised vecs
            if sim >= self.min_similarity:
                candidates.append((self._target_items[idx], sim))

        return candidates

    def _recall_milvus(
        self, source_item: StandardizedItem
    ) -> list[tuple[StandardizedItem, float]]:
        """Search Milvus collection for nearest neighbours."""
        if not hasattr(self, "_milvus_collection"):
            return []

        query_vec = self._encode_items([source_item]).tolist()

        results = self._milvus_collection.search(
            data=query_vec,
            anns_field="embedding",
            param={"metric_type": "IP", "params": {"nprobe": 16}},
            limit=self.top_k,
            output_fields=["item_id"],
        )

        item_lookup = {item.item_id: item for item in self._target_items}
        candidates: list[tuple[StandardizedItem, float]] = []

        for hits in results:
            for hit in hits:
                item_id = hit.entity.get("item_id")
                item = item_lookup.get(item_id)
                if item and hit.score >= self.min_similarity:
                    candidates.append((item, float(hit.score)))

        return candidates
