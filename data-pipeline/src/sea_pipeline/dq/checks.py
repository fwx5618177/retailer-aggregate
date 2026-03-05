"""Data quality checks for the SEA pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DQResult:
    """Outcome of a single DQ check."""

    check_name: str
    passed: bool
    actual_value: float
    threshold: float
    message: str


class DQChecker:
    """Collection of data quality check methods."""

    def check_topn_coverage(
        self,
        items_count: int,
        expected_n: int,
        min_coverage: float = 0.95,
    ) -> DQResult:
        """Verify that we received at least *min_coverage* fraction of expected items."""
        if expected_n == 0:
            return DQResult(
                check_name="topn_coverage",
                passed=True,
                actual_value=1.0,
                threshold=min_coverage,
                message="Expected 0 items; trivially satisfied.",
            )
        coverage = items_count / expected_n
        passed = coverage >= min_coverage
        return DQResult(
            check_name="topn_coverage",
            passed=passed,
            actual_value=round(coverage, 4),
            threshold=min_coverage,
            message=(
                f"Got {items_count}/{expected_n} items (coverage={coverage:.2%}). "
                f"{'PASS' if passed else 'FAIL'}: threshold={min_coverage:.2%}."
            ),
        )

    def check_field_missing_rate(
        self,
        items: list[dict],
        field_name: str,
        max_rate: float = 0.05,
    ) -> DQResult:
        """Check that the fraction of items missing *field_name* is below *max_rate*."""
        if not items:
            return DQResult(
                check_name=f"field_missing_{field_name}",
                passed=True,
                actual_value=0.0,
                threshold=max_rate,
                message=f"No items to check for field '{field_name}'.",
            )
        missing = sum(
            1
            for item in items
            if item.get(field_name) is None or item.get(field_name) == ""
        )
        rate = missing / len(items)
        passed = rate <= max_rate
        return DQResult(
            check_name=f"field_missing_{field_name}",
            passed=passed,
            actual_value=round(rate, 4),
            threshold=max_rate,
            message=(
                f"Field '{field_name}': {missing}/{len(items)} missing (rate={rate:.2%}). "
                f"{'PASS' if passed else 'FAIL'}: max_rate={max_rate:.2%}."
            ),
        )

    def check_rank_uniqueness(
        self,
        items: list[dict],
        platform: str,
    ) -> DQResult:
        """Verify that rank values are unique within a platform."""
        ranks = [item.get("rank") for item in items if item.get("rank") is not None]
        unique_count = len(set(ranks))
        total_count = len(ranks)
        passed = unique_count == total_count
        duplicate_count = total_count - unique_count
        return DQResult(
            check_name=f"rank_uniqueness_{platform}",
            passed=passed,
            actual_value=float(duplicate_count),
            threshold=0.0,
            message=(
                f"Platform '{platform}': {duplicate_count} duplicate ranks out of {total_count}. "
                f"{'PASS' if passed else 'FAIL'}."
            ),
        )

    def check_currency_consistency(
        self,
        items: list[dict],
        expected_currency: str,
    ) -> DQResult:
        """Ensure all items have the expected currency."""
        if not items:
            return DQResult(
                check_name="currency_consistency",
                passed=True,
                actual_value=1.0,
                threshold=1.0,
                message="No items to check currency.",
            )
        mismatches = sum(
            1
            for item in items
            if item.get("currency", "").upper() != expected_currency.upper()
        )
        consistency = 1.0 - (mismatches / len(items))
        passed = mismatches == 0
        return DQResult(
            check_name="currency_consistency",
            passed=passed,
            actual_value=round(consistency, 4),
            threshold=1.0,
            message=(
                f"Currency consistency: {mismatches}/{len(items)} mismatches "
                f"(expected={expected_currency}). {'PASS' if passed else 'FAIL'}."
            ),
        )

    def check_price_range(
        self,
        items: list[dict],
        min_p: int,
        max_p: int,
    ) -> DQResult:
        """Check that all prices fall within [min_p, max_p]."""
        if not items:
            return DQResult(
                check_name="price_range",
                passed=True,
                actual_value=0.0,
                threshold=0.0,
                message="No items to check price range.",
            )
        outliers = 0
        for item in items:
            price = item.get("price", 0)
            if price is not None and (price < min_p or price > max_p):
                outliers += 1
        rate = outliers / len(items)
        passed = outliers == 0
        return DQResult(
            check_name="price_range",
            passed=passed,
            actual_value=round(rate, 4),
            threshold=0.0,
            message=(
                f"Price range [{min_p}, {max_p}]: {outliers}/{len(items)} outliers. "
                f"{'PASS' if passed else 'FAIL'}."
            ),
        )

    def run_all(
        self,
        data: dict[str, Any],
        config: dict[str, Any],
    ) -> list[DQResult]:
        """Run the full suite of DQ checks.

        Parameters
        ----------
        data:
            Must contain keys: ``items`` (list[dict]), ``platform`` (str),
            ``expected_n`` (int), ``currency`` (str).
        config:
            DQ thresholds from the pipeline config (``dq`` section dict).

        Returns
        -------
        list[DQResult]
        """
        items: list[dict] = data.get("items", [])
        platform: str = data.get("platform", "unknown")
        expected_n: int = data.get("expected_n", 200)
        currency: str = data.get("currency", "THB")

        results: list[DQResult] = []

        # 1. Top-N coverage
        results.append(
            self.check_topn_coverage(
                len(items),
                expected_n,
                config.get("topn_coverage_min", 0.95),
            )
        )

        # 2. Field missing rates
        for field_name in ("title", "price", "brand_raw", "item_id"):
            results.append(
                self.check_field_missing_rate(
                    items,
                    field_name,
                    config.get("field_missing_rate_max", 0.05),
                )
            )

        # 3. Rank uniqueness
        if config.get("rank_uniqueness", True):
            results.append(self.check_rank_uniqueness(items, platform))

        # 4. Currency consistency
        if config.get("currency_consistency", True):
            results.append(
                self.check_currency_consistency(items, currency)
            )

        # 5. Price range
        price_range = config.get("price_range", {})
        if isinstance(price_range, dict):
            min_p = price_range.get("min", 100)
            max_p = price_range.get("max", 10_000_000)
        else:
            min_p, max_p = 100, 10_000_000
        results.append(self.check_price_range(items, min_p, max_p))

        return results
