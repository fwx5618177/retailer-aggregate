"""Shared pytest fixtures for the SEA pipeline test suite."""

from __future__ import annotations

import tempfile
from pathlib import Path

import duckdb
import pytest

from sea_pipeline.models.tables import ALL_DDL


@pytest.fixture()
def tmp_duckdb(tmp_path: Path) -> Path:
    """Create a temporary DuckDB database with all tables initialised.

    Returns the path to the ``.duckdb`` file.
    """
    db_path = tmp_path / "test_pipeline.duckdb"
    con = duckdb.connect(str(db_path))
    for ddl in ALL_DDL:
        con.execute(ddl)
    con.close()
    return db_path


@pytest.fixture()
def sample_items() -> list[dict]:
    """Return a list of 10 realistic sample items."""
    return [
        {
            "item_id": f"sh_{1000 + i}",
            "title": title,
            "category": "personal_care",
            "rank": i + 1,
            "url": f"https://shopee.co.th/product/{1000 + i}",
            "image_url": f"https://cf.shopee.co.th/file/{1000 + i}",
            "price": price,
            "promo_price": promo,
            "currency": "THB",
            "brand_raw": brand,
            "review_count": 1000 * (i + 1),
            "sold_range": f"{(i + 1)}K+",
            "rating": round(4.0 + i * 0.08, 1),
        }
        for i, (title, price, promo, brand) in enumerate(
            [
                ("Dove Deeply Nourishing Body Wash 500ml", 19900, 15900, "Dove"),
                ("Nivea Men Deep Clean Face Wash 100g", 14900, 12900, "NIVEA"),
                ("Garnier Micellar Water 400ml", 25900, 19900, "Garnier"),
                ("Pantene Pro-V Shampoo 480ml", 17900, 15900, "PANTENE"),
                ("Sunsilk Smooth & Manageable Shampoo 400ml", 12900, None, "Sunsilk"),
                ("Head & Shoulders Cool Menthol Shampoo 400ml", 18900, 14900, "Head & Shoulders"),
                ("Lux Botanicals Body Wash 500ml", 16900, 13900, "LUX"),
                ("Pond's White Beauty Facial Foam 100g", 9900, 7900, "POND'S"),
                ("Olay Total Effects 7in1 Day Cream 50g", 59900, 49900, "Olay"),
                ("Cetaphil Gentle Skin Cleanser 500ml", 44900, 39900, "cetaphil"),
            ]
        )
    ]


@pytest.fixture()
def stub_config() -> dict:
    """Return a config dictionary suitable for stub-mode testing."""
    return {
        "scope": {
            "platforms": ["shopee"],
            "categories": ["personal_care"],
            "sites": ["th"],
            "top_n": 10,
            "window_days": 14,
        },
        "ingestion": {
            "use_stub": True,
            "stub_fallback": True,
            "rate_limit": {
                "requests_per_second": 2,
                "max_concurrent": 3,
                "backoff_factor": 2.0,
                "max_retries": 3,
            },
        },
        "standardisation": {
            "brand_dictionary_path": "data/brand_dictionary.yaml",
            "unit_rules_path": "data/unit_rules.yaml",
            "spec_tolerance_pct": 10,
        },
        "dq": {
            "mode": "warn",
            "topn_coverage_min": 0.5,
            "field_missing_rate_max": 0.1,
            "rank_uniqueness": True,
            "currency_consistency": True,
            "price_range": {"min": 100, "max": 10000000},
        },
        "storage": {
            "mode": "local",
            "duckdb_path": "data/pipeline.duckdb",
        },
        "export": {
            "serving_dir": "data/serving",
            "format": "parquet",
        },
    }
