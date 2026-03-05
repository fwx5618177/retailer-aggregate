"""Brand + category based candidate recall strategy."""

from __future__ import annotations

from sea_matching.models.match_result import StandardizedItem


class BrandCategoryRecall:
    """Recall candidates based on matching brand and category."""

    def recall(
        self, source_item: StandardizedItem, target_items: list[StandardizedItem]
    ) -> list[tuple[StandardizedItem, float]]:
        """Find candidates from target_items that share brand or category with source_item.

        Returns list of (item, preliminary_score) tuples.
        """
        candidates = []

        source_brand = (source_item.brand_std or "").lower().strip()
        source_category = (source_item.category or "").lower().strip()

        for target in target_items:
            target_brand = (target.brand_std or "").lower().strip()
            target_category = (target.category or "").lower().strip()

            score = 0.0

            # Brand match is the strongest signal
            if source_brand and target_brand and source_brand == target_brand:
                score += 0.6
            elif source_brand and target_brand:
                # Partial brand match (one contains the other)
                if source_brand in target_brand or target_brand in source_brand:
                    score += 0.3

            # Category match
            if source_category and target_category and source_category == target_category:
                score += 0.2

            # Only include if there's some signal
            if score > 0:
                candidates.append((target, score))

        return candidates
