"""Write standardised data into DuckDB tables."""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb

from sea_pipeline.models.tables import ALL_DDL

logger = logging.getLogger("sea_pipeline")


class DuckDBWriter:
    """High-level writer that manages a DuckDB database for the pipeline."""

    def __init__(self, db_path: str | Path = "data/pipeline.duckdb") -> None:
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(self.db_path)

    def init_tables(self) -> None:
        """Create all tables if they do not already exist."""
        con = self._connect()
        try:
            for ddl in ALL_DDL:
                con.execute(ddl)
            logger.info("DuckDB tables initialised at %s", self.db_path)
        finally:
            con.close()

    def write_top_items(self, items: list[dict]) -> int:
        """Insert or replace rows into the ``top_items`` table.

        Returns the number of rows written.
        """
        if not items:
            return 0
        con = self._connect()
        try:
            count = 0
            for item in items:
                con.execute(
                    """
                    INSERT OR REPLACE INTO top_items (
                        event_date, platform, category, site, rank, item_id,
                        title, url, image_url, brand_raw, brand_std,
                        size_value, size_unit, pack_count,
                        normalized_ml, normalized_g,
                        run_id, batch_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        item.get("event_date"),
                        item.get("platform"),
                        item.get("category"),
                        item.get("site"),
                        item.get("rank"),
                        item.get("item_id"),
                        item.get("title"),
                        item.get("url"),
                        item.get("image_url"),
                        item.get("brand_raw"),
                        item.get("brand_std"),
                        item.get("size_value"),
                        item.get("size_unit"),
                        item.get("pack_count", 1),
                        item.get("normalized_ml"),
                        item.get("normalized_g"),
                        item.get("run_id"),
                        item.get("batch_id"),
                    ],
                )
                count += 1
            logger.info("Wrote %d rows to top_items", count)
            return count
        finally:
            con.close()

    def write_price_snapshots(self, snapshots: list[dict]) -> int:
        """Insert or replace rows into the ``price_snapshots`` table."""
        if not snapshots:
            return 0
        con = self._connect()
        try:
            count = 0
            for s in snapshots:
                con.execute(
                    """
                    INSERT OR REPLACE INTO price_snapshots (
                        event_date, platform, item_id,
                        price, promo_price, currency,
                        price_per_ml, price_per_g,
                        run_id, batch_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        s.get("event_date"),
                        s.get("platform"),
                        s.get("item_id"),
                        s.get("price"),
                        s.get("promo_price"),
                        s.get("currency"),
                        s.get("price_per_ml"),
                        s.get("price_per_g"),
                        s.get("run_id"),
                        s.get("batch_id"),
                    ],
                )
                count += 1
            logger.info("Wrote %d rows to price_snapshots", count)
            return count
        finally:
            con.close()

    def write_sales_proxy(self, proxies: list[dict]) -> int:
        """Insert or replace rows into the ``sales_proxy`` table.

        Each dict should have proxy_type, proxy_value, proxy_numeric keys
        (one row per proxy type per item).
        """
        if not proxies:
            return 0
        con = self._connect()
        try:
            count = 0
            for p in proxies:
                con.execute(
                    """
                    INSERT OR REPLACE INTO sales_proxy (
                        event_date, platform, item_id,
                        proxy_type, proxy_value, proxy_numeric,
                        run_id, batch_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        p.get("event_date"),
                        p.get("platform"),
                        p.get("item_id"),
                        p.get("proxy_type"),
                        p.get("proxy_value"),
                        p.get("proxy_numeric"),
                        p.get("run_id"),
                        p.get("batch_id"),
                    ],
                )
                count += 1
            logger.info("Wrote %d rows to sales_proxy", count)
            return count
        finally:
            con.close()

    def write_alerts(self, alerts: list[dict]) -> int:
        """Insert or replace rows into the ``alerts`` table."""
        if not alerts:
            return 0
        con = self._connect()
        try:
            count = 0
            for a in alerts:
                con.execute(
                    """
                    INSERT OR REPLACE INTO alerts (
                        alert_id, event_date, platform, item_id,
                        alert_type, severity, status, message, details,
                        suggested_action, run_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        a.get("alert_id"),
                        a.get("event_date"),
                        a.get("platform"),
                        a.get("item_id"),
                        a.get("alert_type"),
                        a.get("severity"),
                        a.get("status", "open"),
                        a.get("message"),
                        a.get("details"),
                        a.get("suggested_action"),
                        a.get("run_id"),
                    ],
                )
                count += 1
            logger.info("Wrote %d rows to alerts", count)
            return count
        finally:
            con.close()
