"""Currency handling for SEA markets.

Each market has a primary currency and a smallest-unit multiplier
(e.g., THB -> satang, multiply by 100).
"""

from __future__ import annotations


SITE_TO_CURRENCY: dict[str, str] = {
    "th": "THB",
    "sg": "SGD",
    "my": "MYR",
    "id": "IDR",
    "ph": "PHP",
    "vn": "VND",
}

# Multiplier to go from the main currency unit to the smallest unit.
# E.g. 1 THB = 100 satang, 1 SGD = 100 cents, 1 IDR = 1 (no sub-unit in practice).
SMALLEST_UNIT_FACTOR: dict[str, int] = {
    "THB": 100,
    "SGD": 100,
    "MYR": 100,
    "IDR": 1,
    "PHP": 100,
    "VND": 1,
}


class CurrencyHandler:
    """Convert between display amounts and smallest-unit integers."""

    def __init__(self) -> None:
        self.site_to_currency = dict(SITE_TO_CURRENCY)
        self.factors = dict(SMALLEST_UNIT_FACTOR)

    def currency_for_site(self, site: str) -> str:
        """Return the currency code for a given site code."""
        return self.site_to_currency.get(site, "THB")

    def to_smallest_unit(self, amount_float: float, currency: str) -> int:
        """Convert a human-readable amount to the smallest currency unit.

        Example: 199.0 THB -> 19900 (satang).
        """
        factor = self.factors.get(currency.upper(), 100)
        return round(amount_float * factor)

    def from_smallest_unit(self, amount_int: int, currency: str) -> float:
        """Convert a smallest-unit integer back to the display amount.

        Example: 19900 satang -> 199.0 THB.
        """
        factor = self.factors.get(currency.upper(), 100)
        return amount_int / factor
