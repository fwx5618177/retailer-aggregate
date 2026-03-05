"""Write matching results to DuckDB or Parquet."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from sea_matching.models.match_result import MatchCandidate

logger = logging.getLogger(__name__)


class MatchWriter:
    """Write matching results to storage."""

    def write_parquet(
        self,
        candidates: list[MatchCandidate],
        output_dir: str,
        event_date: str,
        run_id: str,
        rule_version: str,
        batch_id: str,
    ) -> str:
        """Write match results to a Parquet file.

        Returns the path to the written file.
        """
        out_path = Path(output_dir) / event_date / run_id
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / "match_map_platform.parquet"

        rows = []
        for c in candidates:
            rows.append({
                "match_id": str(uuid.uuid4()),
                "event_date": c.tiktok_item.event_date or event_date,
                "platform_a": "tiktok",
                "item_id_a": c.tiktok_item.item_id,
                "platform_b": "shopee",
                "item_id_b": c.shopee_item.item_id,
                "brand_std": c.tiktok_item.brand_std or c.shopee_item.brand_std,
                "match_type": c.match_type,
                "confidence": round(c.confidence, 4),
                "status": c.status,
                "reasons": json.dumps(c.reasons.to_dict()),
                "spec_match": (c.scoring_detail.spec_score >= 0.9) if c.scoring_detail else False,
                "price_diff_pct": self._calc_price_diff(c),
                "rule_version": rule_version,
                "run_id": run_id,
                "batch_id": batch_id,
            })

        if not rows:
            logger.warning("No match results to write")
            return str(file_path)

        table = pa.table({
            "match_id": [r["match_id"] for r in rows],
            "event_date": [r["event_date"] for r in rows],
            "platform_a": [r["platform_a"] for r in rows],
            "item_id_a": [r["item_id_a"] for r in rows],
            "platform_b": [r["platform_b"] for r in rows],
            "item_id_b": [r["item_id_b"] for r in rows],
            "brand_std": [r["brand_std"] for r in rows],
            "match_type": [r["match_type"] for r in rows],
            "confidence": [r["confidence"] for r in rows],
            "status": [r["status"] for r in rows],
            "reasons": [r["reasons"] for r in rows],
            "spec_match": [r["spec_match"] for r in rows],
            "price_diff_pct": [r["price_diff_pct"] for r in rows],
            "rule_version": [r["rule_version"] for r in rows],
            "run_id": [r["run_id"] for r in rows],
            "batch_id": [r["batch_id"] for r in rows],
        })

        pq.write_table(table, file_path)
        logger.info("Wrote %d match results to %s", len(rows), file_path)
        return str(file_path)

    def write_duckdb(
        self,
        candidates: list[MatchCandidate],
        db_path: str,
        rule_version: str,
        batch_id: str,
        run_id: str | None = None,
    ) -> int:
        """Write match results to the ``match_map_platform`` table in DuckDB.

        The table is owned by the data-pipeline repo and uses columns
        ``tiktok_item_id`` / ``shopee_item_id``.  If the table does not yet
        exist we create it with that canonical schema so the pipeline,
        API backend, and Streamlit app can all share one DuckDB file.

        Returns the number of rows written.
        """
        effective_run_id = run_id or batch_id
        conn = duckdb.connect(db_path)

        # Canonical schema aligned with data-pipeline/models/tables.py
        conn.execute("""
            CREATE TABLE IF NOT EXISTS match_map_platform (
                tiktok_item_id      VARCHAR     NOT NULL,
                shopee_item_id      VARCHAR     NOT NULL,
                match_type          VARCHAR,
                confidence          DOUBLE,
                status              VARCHAR,
                reasons             VARCHAR,
                rule_version        VARCHAR,
                model_version       VARCHAR,
                event_date          DATE,
                batch_id            VARCHAR,
                run_id              VARCHAR     NOT NULL,
                ingested_at         TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
                schema_version      VARCHAR     DEFAULT '1.0.0',
                PRIMARY KEY (tiktok_item_id, shopee_item_id)
            )
        """)

        count = 0
        for c in candidates:
            event_date = c.tiktok_item.event_date or "1970-01-01"
            conn.execute(
                """INSERT OR REPLACE INTO match_map_platform
                   (tiktok_item_id, shopee_item_id, match_type, confidence,
                    status, reasons, rule_version, event_date, batch_id, run_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    c.tiktok_item.item_id,
                    c.shopee_item.item_id,
                    c.match_type,
                    round(c.confidence, 4),
                    c.status,
                    json.dumps(c.reasons.to_dict()),
                    rule_version,
                    event_date,
                    batch_id,
                    effective_run_id,
                ],
            )
            count += 1

        conn.close()
        logger.info("Wrote %d match results to DuckDB %s", count, db_path)
        return count

    @staticmethod
    def _calc_price_diff(candidate: MatchCandidate) -> float | None:
        """Calculate price difference percentage between two items."""
        tt_price = candidate.tiktok_item.list_price or candidate.tiktok_item.promo_price
        sp_price = candidate.shopee_item.list_price or candidate.shopee_item.promo_price
        if tt_price and sp_price and sp_price > 0:
            return round(abs(tt_price - sp_price) / sp_price * 100, 2)
        return None
