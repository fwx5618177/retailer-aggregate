"""Tests for the SpecParser module."""

from __future__ import annotations

import pytest

from sea_pipeline.standardisation.spec_parser import SpecParser


@pytest.fixture()
def parser() -> SpecParser:
    return SpecParser()


class TestParseML:
    def test_parse_500ml(self, parser: SpecParser) -> None:
        result = parser.parse("Dove Body Wash 500ml")
        assert result.size_value == 500.0
        assert result.size_unit == "ml"
        assert result.normalized_value == 500.0
        assert result.normalized_unit == "ml"

    def test_parse_500_ml_with_space(self, parser: SpecParser) -> None:
        result = parser.parse("Garnier Micellar Water 400 ml")
        assert result.size_value == 400.0
        assert result.size_unit == "ml"
        assert result.normalized_value == 400.0

    def test_parse_200ml(self, parser: SpecParser) -> None:
        result = parser.parse("Nivea Lotion 200ML")
        assert result.size_value == 200.0
        assert result.size_unit == "ml"

    def test_parse_decimal_ml(self, parser: SpecParser) -> None:
        result = parser.parse("Serum 1.5ml Sample")
        assert result.size_value == 1.5
        assert result.size_unit == "ml"
        assert result.normalized_value == 1.5


class TestParseL:
    def test_parse_1L(self, parser: SpecParser) -> None:
        result = parser.parse("Shampoo Refill 1L")
        assert result.size_value == 1.0
        assert result.size_unit == "l"
        assert result.normalized_value == 1000.0
        assert result.normalized_unit == "ml"

    def test_parse_1_liter(self, parser: SpecParser) -> None:
        result = parser.parse("Body Wash 1 Liter Economy Pack")
        assert result.size_value == 1.0
        assert result.size_unit == "liter"
        assert result.normalized_value == 1000.0
        assert result.normalized_unit == "ml"


class TestParseG:
    def test_parse_100g(self, parser: SpecParser) -> None:
        result = parser.parse("Face Wash 100g Tube")
        assert result.size_value == 100.0
        assert result.size_unit == "g"
        assert result.normalized_value == 100.0
        assert result.normalized_unit == "g"

    def test_parse_200g(self, parser: SpecParser) -> None:
        result = parser.parse("Pond's Cream 200g")
        assert result.size_value == 200.0
        assert result.size_unit == "g"
        assert result.normalized_value == 200.0


class TestParseKG:
    def test_parse_1kg(self, parser: SpecParser) -> None:
        result = parser.parse("Detergent Powder 1kg")
        assert result.size_value == 1.0
        assert result.size_unit == "kg"
        assert result.normalized_value == 1000.0
        assert result.normalized_unit == "g"


class TestParseMultipack:
    def test_parse_3x100ml(self, parser: SpecParser) -> None:
        result = parser.parse("Dove Body Wash 3x100ml Value Pack")
        assert result.size_value == 100.0
        assert result.size_unit == "ml"
        assert result.pack_count == 3
        assert result.normalized_value == 300.0

    def test_parse_6x500ml(self, parser: SpecParser) -> None:
        result = parser.parse("Shampoo 6x500ml Carton")
        assert result.size_value == 500.0
        assert result.pack_count == 6
        assert result.normalized_value == 3000.0

    def test_parse_2x200g(self, parser: SpecParser) -> None:
        result = parser.parse("Soap Bar 2x200g")
        assert result.size_value == 200.0
        assert result.size_unit == "g"
        assert result.pack_count == 2
        assert result.normalized_value == 400.0


class TestParseNoSpec:
    def test_no_spec(self, parser: SpecParser) -> None:
        result = parser.parse("Some Random Product Without Size Info")
        assert result.size_value is None
        assert result.size_unit is None
        assert result.normalized_value is None

    def test_empty_string(self, parser: SpecParser) -> None:
        result = parser.parse("")
        assert result.size_value is None

    def test_none_handling(self, parser: SpecParser) -> None:
        # Should not crash
        result = parser.parse("")
        assert result.pack_count == 1


class TestNormalizeToBase:
    def test_l_to_ml(self) -> None:
        value, unit = SpecParser.normalize_to_base(1.0, "l")
        assert value == 1000.0
        assert unit == "ml"

    def test_kg_to_g(self) -> None:
        value, unit = SpecParser.normalize_to_base(1.0, "kg")
        assert value == 1000.0
        assert unit == "g"

    def test_ml_stays_ml(self) -> None:
        value, unit = SpecParser.normalize_to_base(500.0, "ml")
        assert value == 500.0
        assert unit == "ml"
