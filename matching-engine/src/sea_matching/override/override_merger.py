"""Merge existing human overrides into matching results."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from sea_matching.models.match_result import MatchCandidate

logger = logging.getLogger(__name__)


class OverrideMerger:
    """Merge existing override mappings into match results."""

    def __init__(self, overrides_path: str | None = None):
        self.overrides: dict[str, dict] = {}
        if overrides_path:
            self._load(overrides_path)

    def _load(self, path: str) -> None:
        """Load overrides from a JSON file."""
        p = Path(path)
        if not p.exists():
            logger.info("No overrides file found at %s", path)
            return
        with open(p) as f:
            data = json.load(f)
        for override in data.get("overrides", []):
            key = self._make_key(override["tiktok_item_id"], override["shopee_item_id"])
            self.overrides[key] = override
        logger.info("Loaded %d overrides from %s", len(self.overrides), path)

    def _make_key(self, tiktok_id: str, shopee_id: str) -> str:
        return f"{tiktok_id}::{shopee_id}"

    def merge(self, candidates: list[MatchCandidate]) -> list[MatchCandidate]:
        """Apply overrides to matching results.

        If a candidate pair has an override, update its match_type and status to "overridden".
        """
        if not self.overrides:
            return candidates

        for candidate in candidates:
            key = self._make_key(
                candidate.tiktok_item.item_id,
                candidate.shopee_item.item_id,
            )
            if key in self.overrides:
                override = self.overrides[key]
                candidate.match_type = override.get("match_type", candidate.match_type)
                candidate.status = "overridden"
                candidate.reasons.strong_evidence.append(
                    f"Human override applied: {override.get('comment', 'no comment')}"
                )
                logger.info(
                    "Applied override for %s -> %s",
                    candidate.tiktok_item.item_id,
                    candidate.shopee_item.item_id,
                )

        return candidates
