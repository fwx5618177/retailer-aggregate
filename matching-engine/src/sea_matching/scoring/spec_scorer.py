"""Spec (size/weight) closeness scorer."""

from __future__ import annotations

from sea_matching.models.match_result import StandardizedItem


class SpecScorer:
    """Score spec closeness between two items."""

    # Base unit conversion for comparison
    UNIT_TO_BASE = {
        "ml": ("ml", 1.0),
        "l": ("ml", 1000.0),
        "liter": ("ml", 1000.0),
        "g": ("g", 1.0),
        "kg": ("g", 1000.0),
        "oz": ("ml", 29.5735),
        "pcs": ("pcs", 1.0),
        "pack": ("pcs", 1.0),
        "sheets": ("pcs", 1.0),
    }

    def _to_base(self, value: float | None, unit: str | None) -> tuple[float | None, str | None]:
        """Convert a value/unit pair to base units."""
        if value is None or unit is None:
            return None, None
        unit_lower = unit.lower().strip()
        if unit_lower in self.UNIT_TO_BASE:
            base_unit, factor = self.UNIT_TO_BASE[unit_lower]
            return value * factor, base_unit
        return value, unit_lower

    def score(self, item_a: StandardizedItem, item_b: StandardizedItem) -> float:
        """Score spec closeness between two items.

        Returns:
            1.0 for exact spec match
            0.0-1.0 based on normalized difference
            0.5 if specs are incomparable (different unit categories or missing)
        """
        val_a, base_a = self._to_base(item_a.size_value, item_a.size_unit)
        val_b, base_b = self._to_base(item_b.size_value, item_b.size_unit)

        # If either spec is missing, return neutral score
        if val_a is None or val_b is None:
            return 0.5

        # If base units are different categories, not comparable
        if base_a != base_b:
            return 0.3

        # Normalized closeness: 1 - |a - b| / max(a, b)
        max_val = max(val_a, val_b)
        if max_val == 0:
            return 1.0

        diff_ratio = abs(val_a - val_b) / max_val
        return max(0.0, 1.0 - diff_ratio)
