"""End-to-end tests for PipelineRunner using stub data."""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pytest

from sea_pipeline.config import PipelineConfig
from sea_pipeline.runner import PipelineRunner


@pytest.fixture()
def e2e_dir(tmp_path: Path) -> Path:
    """Temporary directory with stub data symlinked."""
    data_dir = tmp_path / "data"
    # Symlink the real stub data
    stub_source = Path(__file__).resolve().parent.parent / "data" / "raw_stub"
    brand_dict = Path(__file__).resolve().parent.parent / "data" / "brand_dictionary.yaml"
    unit_rules = Path(__file__).resolve().parent.parent / "data" / "unit_rules.yaml"

    (data_dir / "raw_stub").mkdir(parents=True, exist_ok=True)

    # Copy stub dirs via symlink
    for platform in ("shopee", "tiktok"):
        src = stub_source / platform
        dst = data_dir / "raw_stub" / platform
        if src.exists():
            os.symlink(src, dst)

    # Copy reference files
    if brand_dict.exists():
        os.symlink(brand_dict, data_dir / "brand_dictionary.yaml")
    if unit_rules.exists():
        os.symlink(unit_rules, data_dir / "unit_rules.yaml")

    return tmp_path


def _make_config(e2e_dir: Path) -> PipelineConfig:
    """Build a PipelineConfig pointing to the temp directory."""
    return PipelineConfig(
        scope={
            "platforms": ["shopee", "tiktok"],
            "categories": ["personal_care"],
            "sites": ["th"],
            "top_n": 200,
            "window_days": 14,
        },
        ingestion={
            "use_stub": True,
            "stub_fallback": True,
        },
        standardisation={
            "brand_dictionary_path": str(e2e_dir / "data" / "brand_dictionary.yaml"),
            "unit_rules_path": str(e2e_dir / "data" / "unit_rules.yaml"),
        },
        dq={
            "mode": "warn",
            "topn_coverage_min": 0.50,
            "field_missing_rate_max": 0.20,
        },
        storage={
            "mode": "local",
            "duckdb_path": str(e2e_dir / "data" / "pipeline.duckdb"),
        },
        export={
            "serving_dir": str(e2e_dir / "data" / "serving"),
            "format": "parquet",
        },
    )


class TestPipelineRunnerE2E:
    """Full pipeline run with stub data."""

    def test_full_stub_run(self, e2e_dir: Path):
        """Run the full pipeline with stub data and verify outputs."""
        # Need to chdir so stub loader finds the right path
        original_cwd = os.getcwd()
        os.chdir(e2e_dir)

        try:
            config = _make_config(e2e_dir)
            runner = PipelineRunner(config)
            manifest = runner.run(
                event_date="2025-02-01",
                run_id="test-e2e-run-001",
            )

            # Pipeline should complete
            assert manifest.run_id == "test-e2e-run-001"
            assert manifest.event_date == "2025-02-01"
            assert manifest.dq_status.lower() in ("passed", "warning")

            # Should have ingested items from both platforms
            db_path = str(e2e_dir / "data" / "pipeline.duckdb")
            con = duckdb.connect(db_path, read_only=True)

            # top_items table should have rows
            top_count = con.execute(
                "SELECT count(*) FROM top_items"
            ).fetchone()[0]
            assert top_count > 0, "No items in top_items table"

            # Both platforms should be present
            platforms = {
                row[0]
                for row in con.execute(
                    "SELECT DISTINCT platform FROM top_items"
                ).fetchall()
            }
            assert "shopee" in platforms
            assert "tiktok" in platforms

            # price_snapshots should have data
            ps_count = con.execute(
                "SELECT count(*) FROM price_snapshots"
            ).fetchone()[0]
            assert ps_count > 0

            # sales_proxy should have data
            sp_count = con.execute(
                "SELECT count(*) FROM sales_proxy"
            ).fetchone()[0]
            assert sp_count > 0

            con.close()

            # Parquet exports should exist
            serving_dir = e2e_dir / "data" / "serving"
            assert serving_dir.exists(), "Serving directory not created"

            # Manifest file should exist
            assert manifest.manifest_path, "Manifest path is empty"
            assert Path(manifest.manifest_path).exists(), "Manifest file not found"

        finally:
            os.chdir(original_cwd)

    def test_single_platform_run(self, e2e_dir: Path):
        """Run pipeline for a single platform."""
        original_cwd = os.getcwd()
        os.chdir(e2e_dir)

        try:
            config = _make_config(e2e_dir)
            config.scope.platforms = ["shopee"]

            runner = PipelineRunner(config)
            manifest = runner.run(
                event_date="2025-02-01",
                run_id="test-single-platform",
            )

            assert manifest.dq_status.lower() in ("passed", "warning")

            db_path = str(e2e_dir / "data" / "pipeline.duckdb")
            con = duckdb.connect(db_path, read_only=True)

            platforms = {
                row[0]
                for row in con.execute(
                    "SELECT DISTINCT platform FROM top_items"
                ).fetchall()
            }
            assert platforms == {"shopee"}
            con.close()

        finally:
            os.chdir(original_cwd)
