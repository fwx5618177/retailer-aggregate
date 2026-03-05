"""Brand matching scorer."""

from __future__ import annotations

from rapidfuzz import fuzz

from sea_matching.models.match_result import StandardizedItem


class BrandScorer:
    """Score brand match between two items."""

    def score(self, item_a: StandardizedItem, item_b: StandardizedItem) -> float:
        """Score brand alignment between two items.

        Returns:
            1.0 for exact match (after standardization)
            0.0-0.9 for fuzzy match on raw brands
            0.0 if either brand is missing
        """
        brand_a = (item_a.brand_std or item_a.brand_raw or "").lower().strip()
        brand_b = (item_b.brand_std or item_b.brand_raw or "").lower().strip()

        if not brand_a or not brand_b:
            return 0.0

        # Exact match on standardized brand
        if brand_a == brand_b:
            return 1.0

        # Fuzzy match on brand names
        similarity = fuzz.ratio(brand_a, brand_b) / 100.0

        # Containment check (e.g., "dove" in "dove beauty")
        if brand_a in brand_b or brand_b in brand_a:
            similarity = max(similarity, 0.85)

        return similarity
