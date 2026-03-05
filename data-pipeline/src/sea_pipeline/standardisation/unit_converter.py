"""General-purpose unit converter with a static conversion table."""

from __future__ import annotations


# Each entry: (from_unit, to_unit) -> factor
CONVERSION_TABLE: dict[tuple[str, str], float] = {
    # Volume
    ("l", "ml"): 1000.0,
    ("ml", "l"): 0.001,
    ("oz", "ml"): 29.5735,
    ("ml", "oz"): 1.0 / 29.5735,
    ("fl_oz", "ml"): 29.5735,
    ("ml", "fl_oz"): 1.0 / 29.5735,
    ("gallon", "ml"): 3785.41,
    ("ml", "gallon"): 1.0 / 3785.41,
    ("gallon", "l"): 3.78541,
    ("l", "gallon"): 1.0 / 3.78541,
    # Weight
    ("kg", "g"): 1000.0,
    ("g", "kg"): 0.001,
    ("lb", "g"): 453.592,
    ("g", "lb"): 1.0 / 453.592,
    ("oz_weight", "g"): 28.3495,
    ("g", "oz_weight"): 1.0 / 28.3495,
    ("lb", "kg"): 0.453592,
    ("kg", "lb"): 1.0 / 0.453592,
}


class UnitConverter:
    """Convert between measurement units using a static conversion table."""

    def __init__(self) -> None:
        self._table = dict(CONVERSION_TABLE)

    def convert(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert *value* from *from_unit* to *to_unit*.

        Raises ``ValueError`` if the conversion is not defined.
        """
        from_u = from_unit.lower().strip()
        to_u = to_unit.lower().strip()

        if from_u == to_u:
            return value

        key = (from_u, to_u)
        if key in self._table:
            return value * self._table[key]

        # Try two-hop through a common base (ml or g)
        for base in ("ml", "g"):
            key_to_base = (from_u, base)
            key_from_base = (base, to_u)
            if key_to_base in self._table and key_from_base in self._table:
                intermediate = value * self._table[key_to_base]
                return intermediate * self._table[key_from_base]

        raise ValueError(
            f"No conversion defined from '{from_unit}' to '{to_unit}'"
        )

    def can_convert(self, from_unit: str, to_unit: str) -> bool:
        """Return True if a conversion path exists."""
        try:
            self.convert(1.0, from_unit, to_unit)
            return True
        except ValueError:
            return False
