"""Write matching run manifest."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ManifestWriter:
    """Write manifest.json for a matching run."""

    def write(
        self,
        output_dir: str,
        event_date: str,
        run_id: str,
        batch_id: str,
        rule_version: str,
        parameters: dict,
        result_counts: dict[str, int],
        duration_seconds: float,
    ) -> str:
        """Write manifest.json to the output directory.

        Returns the path to the manifest file.
        """
        out_path = Path(output_dir) / event_date / run_id
        out_path.mkdir(parents=True, exist_ok=True)
        manifest_path = out_path / "manifest.json"

        manifest = {
            "run_id": run_id,
            "batch_id": batch_id,
            "schema_version": "1.0.0",
            "rule_version": rule_version,
            "model_version": None,
            "created_at": datetime.utcnow().isoformat(),
            "parameters": parameters,
            "result_counts": result_counts,
            "duration_seconds": round(duration_seconds, 2),
        }

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2, default=str)

        logger.info("Wrote manifest to %s", manifest_path)
        return str(manifest_path)
