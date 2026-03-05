"""Local DuckDB storage layer."""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb

from sea_pipeline.models.tables import ALL_DDL

logger = logging.getLogger("sea_pipeline")


class LocalStore:
    """Thin wrapper around a DuckDB database file for ad-hoc queries."""

    def __init__(self, db_path: str | Path = "data/pipeline.duckdb") -> None:
        self.db_path = str(db_path)

    def init_database(self) -> None:
        """Create the database file and all tables."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        con = self.get_connection()
        try:
            for ddl in ALL_DDL:
                con.execute(ddl)
            logger.info("Database initialised at %s", self.db_path)
        finally:
            con.close()

    def get_connection(self, read_only: bool = False) -> duckdb.DuckDBPyConnection:
        """Return a new DuckDB connection."""
        return duckdb.connect(self.db_path, read_only=read_only)

    def query(
        self,
        sql: str,
        params: list | tuple | None = None,
    ) -> list[dict]:
        """Execute *sql* and return rows as a list of dicts."""
        con = self.get_connection(read_only=True)
        try:
            if params:
                result = con.execute(sql, params)
            else:
                result = con.execute(sql)
            columns = [desc[0] for desc in result.description]
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            con.close()
