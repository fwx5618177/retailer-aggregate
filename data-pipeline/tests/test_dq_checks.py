"""Tests for the DQChecker module."""

from __future__ import annotations

import pytest

from sea_pipeline.dq.checks import DQChecker


@pytest.fixture()
def checker() -> DQChecker:
    return DQChecker()


class TestTopNCoverage:
    def test_pass_full_coverage(self, checker: DQChecker) -> None:
        result = checker.check_topn_coverage(200, 200, 0.95)
        assert result.passed is True
        assert result.actual_value == 1.0

    def test_pass_above_threshold(self, checker: DQChecker) -> None:
        result = checker.check_topn_coverage(196, 200, 0.95)
        assert result.passed is True
        assert result.actual_value == 0.98

    def test_fail_below_threshold(self, checker: DQChecker) -> None:
        result = checker.check_topn_coverage(180, 200, 0.95)
        assert result.passed is False
        assert result.actual_value == 0.9

    def test_zero_expected(self, checker: DQChecker) -> None:
        result = checker.check_topn_coverage(0, 0, 0.95)
        assert result.passed is True


class TestFieldMissing:
    def test_pass_no_missing(self, checker: DQChecker) -> None:
        items = [{"title": "Product A"}, {"title": "Product B"}]
        result = checker.check_field_missing_rate(items, "title", 0.05)
        assert result.passed is True
        assert result.actual_value == 0.0

    def test_pass_within_threshold(self, checker: DQChecker) -> None:
        items = [{"title": "A"}, {"title": "B"}, {"title": ""}, *[{"title": f"P{i}"} for i in range(97)]]
        result = checker.check_field_missing_rate(items, "title", 0.05)
        assert result.passed is True

    def test_fail_above_threshold(self, checker: DQChecker) -> None:
        items = [
            {"title": "A"},
            {"title": ""},
            {"title": None},
            {"title": ""},
            {"title": "B"},
        ]
        result = checker.check_field_missing_rate(items, "title", 0.05)
        assert result.passed is False
        # 3 out of 5 missing = 0.6
        assert result.actual_value == 0.6

    def test_missing_key(self, checker: DQChecker) -> None:
        items = [{"title": "A"}, {"other": "B"}]
        result = checker.check_field_missing_rate(items, "title", 0.05)
        assert result.passed is False
        assert result.actual_value == 0.5

    def test_empty_items_list(self, checker: DQChecker) -> None:
        result = checker.check_field_missing_rate([], "title", 0.05)
        assert result.passed is True


class TestRankUniqueness:
    def test_unique_ranks(self, checker: DQChecker) -> None:
        items = [{"rank": i} for i in range(1, 11)]
        result = checker.check_rank_uniqueness(items, "shopee")
        assert result.passed is True
        assert result.actual_value == 0.0

    def test_duplicate_ranks(self, checker: DQChecker) -> None:
        items = [{"rank": 1}, {"rank": 1}, {"rank": 2}]
        result = checker.check_rank_uniqueness(items, "shopee")
        assert result.passed is False
        assert result.actual_value == 1.0  # 1 duplicate

    def test_empty_list(self, checker: DQChecker) -> None:
        result = checker.check_rank_uniqueness([], "shopee")
        assert result.passed is True


class TestCurrencyConsistency:
    def test_all_consistent(self, checker: DQChecker) -> None:
        items = [{"currency": "THB"}, {"currency": "THB"}]
        result = checker.check_currency_consistency(items, "THB")
        assert result.passed is True

    def test_mismatch(self, checker: DQChecker) -> None:
        items = [{"currency": "THB"}, {"currency": "SGD"}]
        result = checker.check_currency_consistency(items, "THB")
        assert result.passed is False


class TestPriceRange:
    def test_within_range(self, checker: DQChecker) -> None:
        items = [{"price": 5000}, {"price": 100000}]
        result = checker.check_price_range(items, 100, 10_000_000)
        assert result.passed is True

    def test_below_range(self, checker: DQChecker) -> None:
        items = [{"price": 50}, {"price": 5000}]
        result = checker.check_price_range(items, 100, 10_000_000)
        assert result.passed is False

    def test_above_range(self, checker: DQChecker) -> None:
        items = [{"price": 20_000_000}]
        result = checker.check_price_range(items, 100, 10_000_000)
        assert result.passed is False
