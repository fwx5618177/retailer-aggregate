"""Price band overlap scorer."""

from __future__ import annotations

from sea_matching.models.match_result import StandardizedItem


class PriceScorer:
    """Score price band similarity between two items."""

    def score(self, item_a: StandardizedItem, item_b: StandardizedItem) -> float:
        """Score price band overlap.

        Uses the effective price (promo_price if available, else list_price).
        Returns 1.0 if prices are very close, decreasing with distance.
        """
        price_a = self._effective_price(item_a)
        price_b = self._effective_price(item_b)

        if price_a is None or price_b is None:
            return 0.5  # Neutral if prices unavailable

        if price_a == 0 and price_b == 0:
            return 1.0

        max_price = max(price_a, price_b)
        if max_price == 0:
            return 0.5

        # Normalized closeness
        diff_ratio = abs(price_a - price_b) / max_price
        # Apply a decay: small differences score high, large differences score low
        # Within 10% = 1.0, within 30% = ~0.7, beyond 50% drops fast
        score = max(0.0, 1.0 - diff_ratio * 2)
        return min(1.0, score)

    def _effective_price(self, item: StandardizedItem) -> int | None:
        """Get the effective price for comparison (promo if available, else list)."""
        if item.promo_price is not None and item.promo_price > 0:
            return item.promo_price
        return item.list_price
