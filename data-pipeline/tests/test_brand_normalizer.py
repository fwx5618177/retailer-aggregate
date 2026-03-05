"""Tests for the BrandNormalizer module."""

from __future__ import annotations

import pytest

from sea_pipeline.standardisation.brand_normalizer import BrandNormalizer


@pytest.fixture()
def normalizer() -> BrandNormalizer:
    return BrandNormalizer("data/brand_dictionary.yaml")


class TestExactMatch:
    def test_standard_name(self, normalizer: BrandNormalizer) -> None:
        assert normalizer.normalize("Dove") == "Dove"

    def test_standard_name_nivea(self, normalizer: BrandNormalizer) -> None:
        assert normalizer.normalize("Nivea") == "Nivea"


class TestVariantMatch:
    def test_thai_dove(self, normalizer: BrandNormalizer) -> None:
        result = normalizer.normalize("โดฟ")
        assert result == "Dove"

    def test_dove_beauty(self, normalizer: BrandNormalizer) -> None:
        result = normalizer.normalize("Dove Beauty")
        assert result == "Dove"

    def test_thai_nivea(self, normalizer: BrandNormalizer) -> None:
        result = normalizer.normalize("นีเวีย")
        assert result == "Nivea"

    def test_ponds_with_apostrophe(self, normalizer: BrandNormalizer) -> None:
        result = normalizer.normalize("pond's")
        assert result == "Pond's"

    def test_loreal_variant(self, normalizer: BrandNormalizer) -> None:
        result = normalizer.normalize("L'Oreal Paris")
        assert result == "L'Oréal"


class TestCaseInsensitive:
    def test_uppercase(self, normalizer: BrandNormalizer) -> None:
        assert normalizer.normalize("DOVE") == "Dove"

    def test_lowercase(self, normalizer: BrandNormalizer) -> None:
        assert normalizer.normalize("dove") == "Dove"

    def test_mixed_case(self, normalizer: BrandNormalizer) -> None:
        assert normalizer.normalize("garnier") == "Garnier"

    def test_uppercase_nivea(self, normalizer: BrandNormalizer) -> None:
        assert normalizer.normalize("NIVEA") == "Nivea"

    def test_cetaphil_lower(self, normalizer: BrandNormalizer) -> None:
        assert normalizer.normalize("cetaphil") == "Cetaphil"


class TestNoMatch:
    def test_unknown_brand(self, normalizer: BrandNormalizer) -> None:
        result = normalizer.normalize("SomeUnknownBrand12345")
        assert result is None

    def test_empty_string(self, normalizer: BrandNormalizer) -> None:
        result = normalizer.normalize("")
        assert result is None

    def test_none_returns_none(self, normalizer: BrandNormalizer) -> None:
        result = normalizer.normalize("")
        assert result is None
