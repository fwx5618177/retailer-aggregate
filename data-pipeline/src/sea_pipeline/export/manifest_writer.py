"""Write a JSON manifest file summarising a pipeline run."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sea_pipeline.dq.checks import DQResult

logger = logging.getLogger("sea_pipeline")


class ManifestWriter:
    """Serialise run metadata to a ``manifest.json`` file."""

    def write(
        self,
        output_dir: str | Path,
        event_date: str,
        run_id: str,
        batch_id: str,
        parameters: dict[str, Any],
        row_counts: dict[str, int],
        dq_results: list[DQResult],
        dq_status: str,
        duration_seconds: float,
    ) -> Path:
        """Write the manifest and return its path.

        The file is placed at ``{output_dir}/{event_date}/{run_id}/manifest.json``.
        """
        dest = Path(output_dir) / event_date / run_id
        dest.mkdir(parents=True, exist_ok=True)
        manifest_path = dest / "manifest.json"

        manifest: dict[str, Any] = {
            "run_id": run_id,
            "batch_id": batch_id,
            "event_date": event_date,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(duration_seconds, 2),
            "parameters": parameters,
            "row_counts": row_counts,
            "dq_status": dq_status,
            "dq_results": [
                {
                    "check_name": r.check_name,
                    "passed": r.passed,
                    "actual_value": r.actual_value,
                    "threshold": r.threshold,
                    "message": r.message,
                }
                for r in dq_results
            ],
        }

        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2, ensure_ascii=False, default=str)

        logger.info("Manifest written to %s", manifest_path)
        return manifest_path
