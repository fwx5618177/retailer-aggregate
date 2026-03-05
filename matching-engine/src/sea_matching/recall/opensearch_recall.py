"""OpenSearch/Elasticsearch based inverted-index candidate recall.

Uses BM25 full-text search on ``brand_std`` and title tokens to generate
recall candidates. This strategy is more scalable than the in-memory TF-IDF
approach for large item catalogs (>10K items).

Requirements:
    pip install opensearch-py  (or elasticsearch)

Configuration (in default.yaml):
    recall:
      strategies:
        - opensearch
      opensearch:
        host: localhost
        port: 9200
        index_name: sea_matching_items
        min_score: 2.0
        top_k: 50

When OpenSearch is not available, the strategy gracefully returns empty
candidates so the pipeline can still run with other recall strategies.
"""

from __future__ import annotations

import logging
from typing import Any

from sea_matching.models.match_result import StandardizedItem

logger = logging.getLogger(__name__)


class OpenSearchRecall:
    """Recall candidates from an OpenSearch/Elasticsearch index."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9200,
        index_name: str = "sea_matching_items",
        min_score: float = 2.0,
        top_k: int = 50,
        use_ssl: bool = False,
        auth: tuple[str, str] | None = None,
    ):
        self.host = host
        self.port = port
        self.index_name = index_name
        self.min_score = min_score
        self.top_k = top_k
        self._client: Any = None
        self._target_items: dict[str, StandardizedItem] = {}
        self._available = False

        try:
            from opensearchpy import OpenSearch

            self._client = OpenSearch(
                hosts=[{"host": host, "port": port}],
                use_ssl=use_ssl,
                http_auth=auth,
                timeout=10,
            )
            # Verify connectivity
            if self._client.ping():
                self._available = True
                logger.info("OpenSearch connected: %s:%d", host, port)
            else:
                logger.warning("OpenSearch not reachable at %s:%d", host, port)
        except ImportError:
            logger.warning(
                "opensearch-py not installed. Run: pip install opensearch-py"
            )
        except Exception as exc:
            logger.warning("OpenSearch connection failed: %s", exc)

    @property
    def available(self) -> bool:
        """Whether OpenSearch is available and connected."""
        return self._available

    def build_index(self, target_items: list[StandardizedItem]) -> None:
        """Index target (Shopee) items into OpenSearch.

        Creates the index with a custom mapping optimised for product matching:
        - ``title``: analysed with standard + Thai analyser
        - ``brand_std``: keyword + text field
        - ``category``: keyword
        """
        if not self._available:
            logger.warning("OpenSearch unavailable — skipping index build")
            return

        # Store items for lookup by item_id
        self._target_items = {item.item_id: item for item in target_items}

        # Delete existing index
        if self._client.indices.exists(index=self.index_name):
            self._client.indices.delete(index=self.index_name)

        # Create index with mapping
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "product_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "trim"],
                        }
                    }
                },
            },
            "mappings": {
                "properties": {
                    "item_id": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "product_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword", "ignore_above": 256}
                        },
                    },
                    "brand_std": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}},
                    },
                    "category": {"type": "keyword"},
                    "size_unit": {"type": "keyword"},
                }
            },
        }

        self._client.indices.create(index=self.index_name, body=mapping)
        logger.info("Created OpenSearch index: %s", self.index_name)

        # Bulk index items
        actions = []
        for item in target_items:
            actions.append(
                {"index": {"_index": self.index_name, "_id": item.item_id}}
            )
            actions.append(
                {
                    "item_id": item.item_id,
                    "title": item.title,
                    "brand_std": item.brand_std or "",
                    "category": item.category,
                    "size_unit": item.size_unit or "",
                }
            )

        if actions:
            from opensearchpy.helpers import bulk

            bulk(self._client, actions)
            self._client.indices.refresh(index=self.index_name)
            logger.info("Indexed %d items into OpenSearch", len(target_items))

    def recall(
        self, source_item: StandardizedItem
    ) -> list[tuple[StandardizedItem, float]]:
        """Search OpenSearch for candidates matching *source_item*.

        Uses a bool query combining:
        - should: multi_match on title (boosted)
        - should: match on brand_std (high boost)
        - filter: same category
        """
        if not self._available:
            return []

        query: dict[str, Any] = {
            "size": self.top_k,
            "min_score": self.min_score,
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": source_item.title,
                                "fields": ["title^2", "title.keyword^3"],
                                "type": "best_fields",
                                "fuzziness": "AUTO",
                            }
                        },
                    ],
                    "filter": [
                        {"term": {"category": source_item.category}},
                    ],
                }
            },
        }

        # Add brand boost if available
        if source_item.brand_std:
            query["query"]["bool"]["should"].append(
                {
                    "match": {
                        "brand_std": {
                            "query": source_item.brand_std,
                            "boost": 5.0,
                        }
                    }
                }
            )

        try:
            response = self._client.search(
                index=self.index_name,
                body=query,
            )
        except Exception as exc:
            logger.warning("OpenSearch query failed: %s", exc)
            return []

        candidates: list[tuple[StandardizedItem, float]] = []
        max_score = response["hits"].get("max_score", 1.0) or 1.0

        for hit in response["hits"]["hits"]:
            item_id = hit["_source"]["item_id"]
            item = self._target_items.get(item_id)
            if item is None:
                continue
            # Normalise score to 0-1 range
            normalised_score = min(hit["_score"] / max_score, 1.0)
            candidates.append((item, normalised_score))

        return candidates
