"""Standardisation result cache — caches title→(brand_std, ParsedSpec) mappings.

Avoids re-running brand normalisation and spec parsing for identical titles
across incremental pipeline runs. The cache is a simple JSON file keyed by
the cleaned (lowercased, stripped) title string.

Thread-safe for single-writer workloads (pipeline runs sequentially).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .spec_parser import ParsedSpec

logger = logging.getLogger(__name__)


class StandardisationCache:
    """LRU-like JSON-file cache for title → standardisation results."""

    def __init__(
        self,
        cache_path: str | Path = "data/std_cache.json",
        max_entries: int = 10_000,
    ) -> None:
        self._path = Path(cache_path)
        self._max_entries = max_entries
        self._data: dict[str, dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0
        self._load()

    def _load(self) -> None:
        """Load cache from disk (if exists)."""
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as fh:
                    raw = json.load(fh)
                if isinstance(raw, dict):
                    self._data = raw
                    logger.info(
                        "Standardisation cache loaded: %d entries from %s",
                        len(self._data),
                        self._path,
                    )
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Failed to load std cache: %s", exc)
                self._data = {}

    def save(self) -> None:
        """Persist cache to disk. Trims to max_entries (keeps most-recent)."""
        # Trim if over limit (keep newest entries based on insertion order)
        if len(self._data) > self._max_entries:
            keys = list(self._data.keys())
            trim_count = len(keys) - self._max_entries
            for k in keys[:trim_count]:
                del self._data[k]

        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, ensure_ascii=False, indent=None)
        logger.info(
            "Standardisation cache saved: %d entries (hits=%d, misses=%d)",
            len(self._data),
            self._hits,
            self._misses,
        )

    @staticmethod
    def _make_key(title: str) -> str:
        """Normalise key: lowercase + collapse whitespace."""
        return " ".join(title.strip().lower().split())

    def get(self, title: str) -> tuple[str | None, ParsedSpec] | None:
        """Retrieve cached (brand_std, ParsedSpec) for *title*, or None."""
        key = self._make_key(title)
        entry = self._data.get(key)
        if entry is None:
            self._misses += 1
            return None

        self._hits += 1
        brand_std = entry.get("brand_std")
        spec = ParsedSpec(
            size_value=entry.get("size_value"),
            size_unit=entry.get("size_unit"),
            pack_count=entry.get("pack_count", 1),
            normalized_value=entry.get("normalized_value"),
            normalized_unit=entry.get("normalized_unit"),
        )
        return brand_std, spec

    def put(
        self,
        title: str,
        brand_std: str | None,
        spec: ParsedSpec,
    ) -> None:
        """Store standardisation result for *title*."""
        key = self._make_key(title)
        self._data[key] = {
            "brand_std": brand_std,
            "size_value": spec.size_value,
            "size_unit": spec.size_unit,
            "pack_count": spec.pack_count,
            "normalized_value": spec.normalized_value,
            "normalized_unit": spec.normalized_unit,
        }

    @property
    def stats(self) -> dict[str, int]:
        """Return cache hit/miss statistics."""
        return {
            "size": len(self._data),
            "hits": self._hits,
            "misses": self._misses,
        }
