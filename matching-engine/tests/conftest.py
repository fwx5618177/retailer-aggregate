"""Shared test fixtures for matching engine."""

import pytest

from sea_matching.models.match_result import StandardizedItem


@pytest.fixture
def dove_tiktok():
    return StandardizedItem(
        platform="tiktok",
        item_id="tt_001",
        title="Dove Deeply Nourishing Body Wash 500ml",
        category="personal_care",
        rank=1,
        brand_raw="Dove",
        brand_std="Dove",
        size_value=500.0,
        size_unit="ml",
        list_price=19900,
        currency="THB",
    )


@pytest.fixture
def dove_shopee():
    return StandardizedItem(
        platform="shopee",
        item_id="sh_001",
        title="Dove Body Wash Deeply Nourishing 500ml Bottle",
        category="personal_care",
        rank=3,
        brand_raw="DOVE",
        brand_std="Dove",
        size_value=500.0,
        size_unit="ml",
        list_price=19500,
        currency="THB",
    )


@pytest.fixture
def dove_variant_shopee():
    return StandardizedItem(
        platform="shopee",
        item_id="sh_002",
        title="Dove Body Wash Deeply Nourishing 200ml",
        category="personal_care",
        rank=15,
        brand_raw="Dove",
        brand_std="Dove",
        size_value=200.0,
        size_unit="ml",
        list_price=9900,
        currency="THB",
    )


@pytest.fixture
def nivea_shopee():
    return StandardizedItem(
        platform="shopee",
        item_id="sh_003",
        title="Nivea Extra White Body Lotion 400ml",
        category="personal_care",
        rank=5,
        brand_raw="NIVEA",
        brand_std="Nivea",
        size_value=400.0,
        size_unit="ml",
        list_price=17900,
        currency="THB",
    )


@pytest.fixture
def sample_shopee_items(dove_shopee, dove_variant_shopee, nivea_shopee):
    return [dove_shopee, dove_variant_shopee, nivea_shopee]
