"""Raw response cache -- persists API responses as JSON files on disk."""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

logger = logging.getLogger("sea_pipeline")


class RawCache:
    """File-based cache stored under ``{cache_dir}/{platform}/{category}/{date}.json``."""

    def __init__(self, cache_dir: str | Path = "data/raw_cache") -> None:
        self.cache_dir = Path(cache_dir)

    def _path(self, platform: str, category: str, event_date: date | str) -> Path:
        if isinstance(event_date, date):
            event_date = event_date.isoformat()
        return self.cache_dir / platform / category / f"{event_date}.json"

    def save(
        self,
        platform: str,
        category: str,
        event_date: date | str,
        data: list[dict] | dict,
    ) -> Path:
        """Persist *data* to JSON and return the file path."""
        path = self._path(platform, category, event_date)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2, default=str)
        logger.debug("Cached %s/%s/%s -> %s", platform, category, event_date, path)
        return path

    def load(
        self,
        platform: str,
        category: str,
        event_date: date | str,
    ) -> list[dict] | None:
        """Load cached data, returning ``None`` if not found."""
        path = self._path(platform, category, event_date)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def has(
        self,
        platform: str,
        category: str,
        event_date: date | str,
    ) -> bool:
        """Return ``True`` if the cache file exists."""
        return self._path(platform, category, event_date).exists()
