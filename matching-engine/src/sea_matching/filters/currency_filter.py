"""Currency/site consistency filter."""

from __future__ import annotations

from sea_matching.models.match_result import MatchCandidate


class CurrencyFilter:
    """Filter candidates based on currency consistency."""

    def __init__(self, require_same_currency: bool = True):
        self.require_same = require_same_currency

    def filter(self, candidates: list[MatchCandidate]) -> list[MatchCandidate]:
        """Remove candidates where currencies don't match (if required)."""
        if not self.require_same:
            return candidates

        filtered = []
        for candidate in candidates:
            src_curr = candidate.tiktok_item.currency
            tgt_curr = candidate.shopee_item.currency

            # If either lacks currency, allow through
            if not src_curr or not tgt_curr:
                filtered.append(candidate)
                continue

            if src_curr.upper() == tgt_curr.upper():
                filtered.append(candidate)

        return filtered
