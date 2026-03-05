"""Title similarity scorer using RapidFuzz."""

from __future__ import annotations

import re

from rapidfuzz import fuzz

from sea_matching.models.match_result import StandardizedItem


def _clean_title(title: str) -> str:
    """Clean title for comparison: lowercase, remove special chars, normalize whitespace."""
    title = title.lower()
    # Remove common noise words
    noise = [
        "official", "store", "shop", "100%", "authentic", "original",
        "free shipping", "hot sale", "best seller", "new arrival",
        "cod", "ready stock",
    ]
    for word in noise:
        title = title.replace(word, "")
    title = re.sub(r"[^\w\s\u0e00-\u0e7f]", " ", title)  # Keep Thai
    title = re.sub(r"\s+", " ", title).strip()
    return title


class TitleScorer:
    """Score title similarity between two items."""

    def __init__(self, method: str = "token_sort_ratio"):
        self.method = method

    def score(self, item_a: StandardizedItem, item_b: StandardizedItem) -> float:
        """Score title similarity.

        Returns 0.0-1.0 based on string similarity.
        """
        title_a = _clean_title(item_a.title)
        title_b = _clean_title(item_b.title)

        if not title_a or not title_b:
            return 0.0

        if self.method == "token_sort_ratio":
            return fuzz.token_sort_ratio(title_a, title_b) / 100.0
        elif self.method == "partial_ratio":
            return fuzz.partial_ratio(title_a, title_b) / 100.0
        elif self.method == "token_set_ratio":
            return fuzz.token_set_ratio(title_a, title_b) / 100.0
        else:
            # Default to token_sort_ratio
            return fuzz.token_sort_ratio(title_a, title_b) / 100.0
