"""Stub data loader -- reads pre-saved JSON files for offline / test runs."""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from pathlib import Path

logger = logging.getLogger("sea_pipeline")


class StubLoader:
    """Load stub JSON files from ``data/raw_stub/{platform}/{category}/``."""

    def __init__(self, stub_root: str | Path = "data/raw_stub") -> None:
        self.stub_root = Path(stub_root)

    def load(
        self,
        platform: str,
        category: str,
        event_date: date | str,
    ) -> list[dict]:
        """Return items from the stub file for the given date.

        If the exact date file does not exist, falls back to the most recent
        available file within the same directory.
        """
        if isinstance(event_date, str):
            event_date = date.fromisoformat(event_date)

        target_dir = self.stub_root / platform / category
        exact_path = target_dir / f"{event_date.isoformat()}.json"

        if exact_path.exists():
            return self._read(exact_path)

        # Fallback: pick the closest earlier file
        fallback = self._find_nearest(target_dir, event_date)
        if fallback is not None:
            logger.warning(
                "Stub file for %s not found; falling back to %s",
                event_date.isoformat(),
                fallback.name,
            )
            return self._read(fallback)

        logger.error(
            "No stub data found for %s/%s in %s", platform, category, target_dir,
        )
        return []

    # ------------------------------------------------------------------

    @staticmethod
    def _read(path: Path) -> list[dict]:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "items" in data:
            return data["items"]
        return [data]

    @staticmethod
    def _find_nearest(directory: Path, target: date) -> Path | None:
        """Return the JSON file whose date-stem is closest to *target*."""
        if not directory.is_dir():
            return None
        candidates: list[tuple[int, Path]] = []
        for p in directory.glob("*.json"):
            try:
                file_date = date.fromisoformat(p.stem)
            except ValueError:
                continue
            delta = abs((target - file_date).days)
            candidates.append((delta, p))
        if not candidates:
            return None
        candidates.sort(key=lambda t: t[0])
        return candidates[0][1]
