"""Export DuckDB tables to Parquet files for downstream consumption."""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb

logger = logging.getLogger("sea_pipeline")

EXPORT_TABLES = [
    "top_items",
    "price_snapshots",
    "sales_proxy",
    "match_map_platform",
    "our_mapping",
    "alerts",
]


class ParquetExporter:
    """Reads each table from DuckDB and writes Parquet files to the serving directory."""

    def export_to_parquet(
        self,
        db_path: str | Path,
        output_dir: str | Path,
        event_date: str,
        run_id: str,
    ) -> dict[str, int]:
        """Export all tables for a specific run to Parquet.

        Files are written to ``{output_dir}/{event_date}/{run_id}/{table}.parquet``.

        Returns a dict mapping table name to row count exported.
        """
        dest = Path(output_dir) / event_date / run_id
        dest.mkdir(parents=True, exist_ok=True)

        con = duckdb.connect(str(db_path), read_only=True)
        row_counts: dict[str, int] = {}

        try:
            for table in EXPORT_TABLES:
                # Check if the table has any rows
                try:
                    count_result = con.execute(
                        f"SELECT COUNT(*) FROM {table}"
                    ).fetchone()
                except duckdb.CatalogException:
                    logger.debug("Table %s does not exist, skipping.", table)
                    continue

                row_count = count_result[0] if count_result else 0
                if row_count == 0:
                    logger.debug("Table %s is empty, skipping Parquet export.", table)
                    row_counts[table] = 0
                    continue

                parquet_path = dest / f"{table}.parquet"
                con.execute(
                    f"COPY {table} TO '{parquet_path}' (FORMAT PARQUET)"
                )
                row_counts[table] = row_count
                logger.info(
                    "Exported %s -> %s (%d rows)", table, parquet_path, row_count,
                )
        finally:
            con.close()

        return row_counts
