"""Data loader for Streamlit app - reads from DuckDB.

All paths are derived from the project root to ensure correctness
regardless of which directory the process is started from.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

# Derive the project root from this file's location:
# loader.py is at <project_root>/app-mvp/src/app/data/loader.py
_PROJECT_ROOT = Path(__file__).resolve().parents[4]

DB_PATH = str(_PROJECT_ROOT / "data-pipeline" / "data" / "pipeline.duckdb")
DATA_PIPELINE_DIR = str(_PROJECT_ROOT / "data-pipeline")
MATCHING_ENGINE_DIR = str(_PROJECT_ROOT / "matching-engine")


def get_db_connection(db_path: str = DB_PATH, read_only: bool = True):
    """Get DuckDB connection."""
    if not Path(db_path).exists():
        return None
    return duckdb.connect(db_path, read_only=read_only)


def load_overview_stats(stub: bool = True, db_path: str = DB_PATH) -> dict | None:
    """Load overview statistics from DuckDB."""
    conn = get_db_connection(db_path)
    if conn is None:
        return None

    try:
        tt_count = conn.execute(
            "SELECT COUNT(*) FROM top_items WHERE platform='tiktok'"
        ).fetchone()[0]
        sh_count = conn.execute(
            "SELECT COUNT(*) FROM top_items WHERE platform='shopee'"
        ).fetchone()[0]

        try:
            matched = conn.execute(
                "SELECT COUNT(*) FROM match_map_platform WHERE status != 'no_match'"
            ).fetchone()[0]
            needs_review = conn.execute(
                "SELECT COUNT(*) FROM match_map_platform WHERE status = 'needs_review'"
            ).fetchone()[0]
            match_rate = matched / max(tt_count, 1) * 100
        except Exception:
            matched = 0
            needs_review = 0
            match_rate = 0

        return {
            "tiktok_count": tt_count,
            "shopee_count": sh_count,
            "matched": matched,
            "needs_review": needs_review,
            "match_rate": match_rate,
        }
    except Exception:
        return None
    finally:
        conn.close()


def load_top_items(
    db_path: str = DB_PATH,
    platform: str | None = None,
    brand: str | None = None,
    limit: int = 200,
) -> pd.DataFrame:
    """Load top items with optional filters."""
    conn = get_db_connection(db_path)
    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT t.*, p.price AS list_price, p.promo_price, p.currency
            FROM top_items t
            LEFT JOIN price_snapshots p
                ON t.platform = p.platform AND t.item_id = p.item_id AND t.event_date = p.event_date
            WHERE 1=1
        """
        params = []
        if platform:
            query += " AND t.platform = ?"
            params.append(platform)
        if brand:
            query += " AND t.brand_std = ?"
            params.append(brand)
        query += f" ORDER BY t.platform, t.rank LIMIT {limit}"

        return conn.execute(query, params).fetchdf()
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()


def load_all_data(db_path: str = DB_PATH) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load top_items, match_map, and price_snapshots for overview."""
    conn = get_db_connection(db_path)
    if conn is None:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    try:
        top_items = conn.execute("SELECT * FROM top_items").fetchdf()
        match_map = conn.execute("SELECT * FROM match_map_platform").fetchdf()
        prices = conn.execute("SELECT * FROM price_snapshots").fetchdf()
        return top_items, match_map, prices
    except Exception:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    finally:
        conn.close()


def load_traceability(db_path: str = DB_PATH) -> dict | None:
    """Load traceability metadata from DuckDB (latest run_id, event_date, etc.)."""
    conn = get_db_connection(db_path)
    if conn is None:
        return None

    try:
        row = conn.execute(
            "SELECT event_date, run_id, batch_id FROM top_items "
            "ORDER BY ingested_at DESC LIMIT 1"
        ).fetchone()
        if not row:
            return None

        event_date, run_id, batch_id = row

        # Get rule_version and schema_version from match_map if available
        rule_version = "1.0.0"
        schema_version = "1.0.0"
        try:
            mrow = conn.execute(
                "SELECT rule_version, schema_version FROM match_map_platform LIMIT 1"
            ).fetchone()
            if mrow:
                rule_version = mrow[0] or "1.0.0"
                schema_version = mrow[1] or "1.0.0"
        except Exception:
            pass

        return {
            "event_date": str(event_date),
            "run_id": str(run_id),
            "batch_id": str(batch_id),
            "rule_version": rule_version,
            "schema_version": schema_version,
        }
    except Exception:
        return None
    finally:
        conn.close()


def load_data_quality_summary(db_path: str = DB_PATH) -> dict | None:
    """Check data quality indicators for degraded data warnings."""
    conn = get_db_connection(db_path)
    if conn is None:
        return None

    try:
        total = conn.execute("SELECT COUNT(*) FROM top_items").fetchone()[0]
        if total == 0:
            return {"status": "empty", "message": "No data loaded"}

        # Check for missing critical fields
        missing_title = conn.execute(
            "SELECT COUNT(*) FROM top_items WHERE title IS NULL OR title = ''"
        ).fetchone()[0]
        missing_brand = conn.execute(
            "SELECT COUNT(*) FROM top_items WHERE brand_raw IS NULL OR brand_raw = ''"
        ).fetchone()[0]
        missing_price = conn.execute(
            "SELECT COUNT(*) FROM price_snapshots WHERE price IS NULL OR price <= 0"
        ).fetchone()[0]

        title_pct = missing_title / total * 100
        brand_pct = missing_brand / total * 100
        price_pct = missing_price / max(total, 1) * 100

        issues = []
        if title_pct > 5:
            issues.append(f"Title missing: {title_pct:.1f}%")
        if brand_pct > 10:
            issues.append(f"Brand missing: {brand_pct:.1f}%")
        if price_pct > 5:
            issues.append(f"Price invalid: {price_pct:.1f}%")

        if issues:
            return {
                "status": "degraded",
                "message": "Data quality issues: " + "; ".join(issues),
            }
        return {"status": "ok", "message": "All quality checks passed"}
    except Exception:
        return None
    finally:
        conn.close()


def load_alerts(db_path: str = DB_PATH) -> pd.DataFrame:
    """Load alerts from DuckDB."""
    conn = get_db_connection(db_path)
    if conn is None:
        return pd.DataFrame()

    try:
        return conn.execute(
            "SELECT * FROM alerts ORDER BY severity, event_date DESC"
        ).fetchdf()
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()


def load_review_queue(db_path: str = DB_PATH) -> pd.DataFrame:
    """Load review queue from DuckDB."""
    conn = get_db_connection(db_path)
    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT
                m.tiktok_item_id, m.shopee_item_id,
                m.match_type, m.confidence, m.status, m.reasons,
                tt.title as tiktok_title, tt.brand_std as tiktok_brand,
                tt.size_value as tiktok_size, tt.size_unit as tiktok_unit,
                sh.title as shopee_title, sh.brand_std as shopee_brand,
                sh.size_value as shopee_size, sh.size_unit as shopee_unit
            FROM match_map_platform m
            LEFT JOIN top_items tt ON m.tiktok_item_id = tt.item_id AND tt.platform = 'tiktok'
            LEFT JOIN top_items sh ON m.shopee_item_id = sh.item_id AND sh.platform = 'shopee'
            WHERE m.status = 'needs_review'
            ORDER BY m.confidence DESC
        """
        return conn.execute(query).fetchdf()
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()
