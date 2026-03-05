"""Extract size / volume / weight specifications from product titles."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ParsedSpec:
    """Result of parsing a product title for spec information."""

    size_value: float | None = None
    size_unit: str | None = None
    pack_count: int = 1
    normalized_value: float | None = None
    normalized_unit: str | None = None


# Conversion factors to base units (ml for volume, g for weight)
_TO_BASE: dict[str, tuple[float, str]] = {
    "ml": (1.0, "ml"),
    "มล": (1.0, "ml"),
    "l": (1000.0, "ml"),
    "liter": (1000.0, "ml"),
    "litre": (1000.0, "ml"),
    "ลิตร": (1000.0, "ml"),
    "oz": (29.5735, "ml"),
    "fl oz": (29.5735, "ml"),
    "g": (1.0, "g"),
    "กรัม": (1.0, "g"),
    "gm": (1.0, "g"),
    "gr": (1.0, "g"),
    "kg": (1000.0, "g"),
    "กก": (1000.0, "g"),
    "lb": (453.592, "g"),
    "pcs": (1.0, "pcs"),
    "sheets": (1.0, "pcs"),
    "capsules": (1.0, "pcs"),
    "tablets": (1.0, "pcs"),
}

# Regex unit alternatives (longest first to avoid partial matches)
_UNIT_PATTERN = (
    r"(?:ml|มล\.?|liter|litre|ลิตร|fl\s?oz|oz|kg|กก\.?|กรัม|gm|gr|g|l|lb|pcs|sheets|capsules|tablets)"
)

# Main patterns, ordered from most specific to least specific
_PATTERNS: list[re.Pattern[str]] = [
    # Multipack: "3x100ml", "6 x 100 ml", "3X500ML"
    re.compile(
        rf"(\d+)\s*[xX]\s*(\d+(?:\.\d+)?)\s*({_UNIT_PATTERN})",
        re.IGNORECASE,
    ),
    # Pack notation: "6 Pack 100ml", "3 Pack"
    re.compile(
        rf"(\d+)\s*(?:pack|แพ็ค|แพค|กล่อง)\s+(\d+(?:\.\d+)?)\s*({_UNIT_PATTERN})",
        re.IGNORECASE,
    ),
    # Standard: "500ml", "500 ml", "1.5L", "200 g"
    re.compile(
        rf"(\d+(?:\.\d+)?)\s*({_UNIT_PATTERN})\b",
        re.IGNORECASE,
    ),
    # Thai style with มล / กรัม at end: "500 มล.", "200 กรัม"
    re.compile(
        rf"(\d+(?:\.\d+)?)\s*(มล\.?|กรัม|กก\.?|ลิตร)",
        re.IGNORECASE,
    ),
]


def _normalize_unit(raw_unit: str) -> str:
    """Map a raw unit string to a canonical lowercase key for _TO_BASE."""
    u = raw_unit.strip().lower().rstrip(".")
    # Handle Thai units
    mapping = {
        "มล": "ml",
        "กรัม": "g",
        "กก": "kg",
        "ลิตร": "l",
    }
    return mapping.get(u, u)


class SpecParser:
    """Parse product titles to extract size, unit, and pack information."""

    def parse(self, title: str) -> ParsedSpec:
        """Parse *title* and return a ``ParsedSpec``.

        Tries multipack patterns first, then standard size patterns.
        """
        if not title:
            return ParsedSpec()

        for pattern in _PATTERNS:
            match = pattern.search(title)
            if match is None:
                continue

            groups = match.groups()

            if len(groups) == 3 and pattern is _PATTERNS[0]:
                # Multipack: count x value unit
                pack_count = int(groups[0])
                size_value = float(groups[1])
                raw_unit = groups[2]
            elif len(groups) == 3 and pattern is _PATTERNS[1]:
                # Pack + value unit
                pack_count = int(groups[0])
                size_value = float(groups[1])
                raw_unit = groups[2]
            else:
                # Standard: value unit
                pack_count = 1
                size_value = float(groups[0])
                raw_unit = groups[1]

            unit_key = _normalize_unit(raw_unit)
            base_factor, base_unit = _TO_BASE.get(unit_key, (1.0, unit_key))
            normalized_value = size_value * base_factor * pack_count

            return ParsedSpec(
                size_value=size_value,
                size_unit=unit_key,
                pack_count=pack_count,
                normalized_value=normalized_value,
                normalized_unit=base_unit,
            )

        # Also check for a bare "Pack" without size
        pack_match = re.search(r"(\d+)\s*(?:pack|แพ็ค|แพค)", title, re.IGNORECASE)
        if pack_match:
            return ParsedSpec(pack_count=int(pack_match.group(1)))

        return ParsedSpec()

    @staticmethod
    def normalize_to_base(value: float, unit: str) -> tuple[float, str]:
        """Convert *value* in *unit* to its base unit (ml or g).

        Returns (base_value, base_unit).
        """
        unit_key = _normalize_unit(unit)
        factor, base_unit = _TO_BASE.get(unit_key, (1.0, unit_key))
        return value * factor, base_unit
