"""Combined recall that merges results from multiple strategies."""

from __future__ import annotations

import logging

from sea_matching.models.match_result import StandardizedItem
from sea_matching.recall.brand_category_recall import BrandCategoryRecall
from sea_matching.recall.text_recall import TextRecall

logger = logging.getLogger(__name__)


class CombinedRecall:
    """Combines multiple recall strategies and deduplicates results.

    Supported strategies:
    - ``brand_category``: Brand + category blocking (always available)
    - ``text_similarity``: TF-IDF or RapidFuzz text recall (always available)
    - ``opensearch``: BM25 via OpenSearch/Elasticsearch (optional, graceful fallback)
    - ``vector``: Dense vector recall via FAISS or Milvus (optional, graceful fallback)
    """

    def __init__(
        self,
        strategies: list[str],
        top_k: int = 20,
        text_config: dict | None = None,
        opensearch_config: dict | None = None,
        vector_config: dict | None = None,
    ):
        self.top_k = top_k
        self._strategies: list[str] = strategies
        self._brand_recall = BrandCategoryRecall()
        text_cfg = text_config or {}
        self._text_recall = TextRecall(
            method=text_cfg.get("method", "tfidf"),
            min_similarity=text_cfg.get("min_similarity", 0.3),
        )

        # Optional: OpenSearch recall
        self._opensearch_recall = None
        if "opensearch" in strategies:
            os_cfg = opensearch_config or {}
            try:
                from sea_matching.recall.opensearch_recall import OpenSearchRecall

                self._opensearch_recall = OpenSearchRecall(
                    host=os_cfg.get("host", "localhost"),
                    port=os_cfg.get("port", 9200),
                    index_name=os_cfg.get("index_name", "sea_matching_items"),
                    min_score=os_cfg.get("min_score", 2.0),
                    top_k=os_cfg.get("top_k", 50),
                )
                if not self._opensearch_recall.available:
                    logger.warning(
                        "OpenSearch configured but not available — "
                        "falling back to other strategies"
                    )
            except Exception as exc:
                logger.warning("Failed to initialise OpenSearch recall: %s", exc)

        # Optional: Vector recall
        self._vector_recall = None
        if "vector" in strategies:
            vec_cfg = vector_config or {}
            try:
                from sea_matching.recall.vector_recall import VectorRecall

                self._vector_recall = VectorRecall(
                    backend=vec_cfg.get("backend", "local"),
                    model_name=vec_cfg.get(
                        "model_name",
                        "paraphrase-multilingual-MiniLM-L12-v2",
                    ),
                    top_k=vec_cfg.get("top_k", 30),
                    min_similarity=vec_cfg.get("min_similarity", 0.4),
                    milvus_host=vec_cfg.get("milvus_host", "localhost"),
                    milvus_port=vec_cfg.get("milvus_port", 19530),
                    collection_name=vec_cfg.get(
                        "collection_name", "sea_matching_vectors"
                    ),
                )
                if not self._vector_recall.available:
                    logger.warning(
                        "Vector recall configured but model not available — "
                        "falling back to other strategies"
                    )
            except Exception as exc:
                logger.warning("Failed to initialise vector recall: %s", exc)

    def build_index(self, target_items: list[StandardizedItem]) -> None:
        """Build indices for all strategies that need them."""
        if "text_similarity" in self._strategies:
            self._text_recall.build_index(target_items)

        if self._opensearch_recall and self._opensearch_recall.available:
            self._opensearch_recall.build_index(target_items)

        if self._vector_recall and self._vector_recall.available:
            self._vector_recall.build_index(target_items)

    def recall(
        self,
        source_item: StandardizedItem,
        target_items: list[StandardizedItem],
    ) -> list[tuple[StandardizedItem, float]]:
        """Run all recall strategies, merge, deduplicate, and return top-K."""
        candidates: dict[str, tuple[StandardizedItem, float]] = {}

        if "brand_category" in self._strategies:
            for item, score in self._brand_recall.recall(source_item, target_items):
                key = item.item_id
                if key not in candidates or candidates[key][1] < score:
                    candidates[key] = (item, score)

        if "text_similarity" in self._strategies:
            for item, score in self._text_recall.recall(source_item):
                key = item.item_id
                if key not in candidates:
                    candidates[key] = (item, score)
                else:
                    existing_score = candidates[key][1]
                    if score > existing_score:
                        candidates[key] = (item, score)

        # OpenSearch recall (optional)
        if self._opensearch_recall and self._opensearch_recall.available:
            try:
                for item, score in self._opensearch_recall.recall(source_item):
                    key = item.item_id
                    if key not in candidates or candidates[key][1] < score:
                        candidates[key] = (item, score)
            except Exception as exc:
                logger.warning("OpenSearch recall failed: %s", exc)

        # Vector recall (optional)
        if self._vector_recall and self._vector_recall.available:
            try:
                for item, score in self._vector_recall.recall(source_item):
                    key = item.item_id
                    if key not in candidates or candidates[key][1] < score:
                        candidates[key] = (item, score)
            except Exception as exc:
                logger.warning("Vector recall failed: %s", exc)

        # Sort by preliminary score descending, take top K
        sorted_candidates = sorted(
            candidates.values(), key=lambda x: x[1], reverse=True
        )
        return sorted_candidates[: self.top_k]
