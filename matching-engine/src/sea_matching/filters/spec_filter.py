"""Spec tolerance filter - removes candidates where specs differ too much."""

from __future__ import annotations

from sea_matching.models.match_result import MatchCandidate


class SpecFilter:
    """Filter candidates based on spec (size/weight) tolerance."""

    def __init__(self, tolerance_pct: float = 10.0):
        self.tolerance_pct = tolerance_pct

    def filter(self, candidates: list[MatchCandidate]) -> list[MatchCandidate]:
        """Remove candidates where specs differ beyond tolerance.

        If either item lacks spec data, the candidate passes through (no filter applied).
        """
        filtered = []
        for candidate in candidates:
            src = candidate.tiktok_item
            tgt = candidate.shopee_item

            # If either item lacks spec data, allow through
            if src.size_value is None or tgt.size_value is None:
                filtered.append(candidate)
                continue

            # If units don't match, allow through (scorer will handle unit mismatch)
            if src.size_unit != tgt.size_unit:
                filtered.append(candidate)
                continue

            # Check tolerance
            if src.size_value == 0:
                filtered.append(candidate)
                continue

            diff_pct = abs(src.size_value - tgt.size_value) / src.size_value * 100
            if diff_pct <= self.tolerance_pct:
                filtered.append(candidate)

        return filtered
