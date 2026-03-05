"""Generate evaluation reports from matching results."""

from __future__ import annotations

import json
import logging
import random
from datetime import datetime
from pathlib import Path

from sea_matching.models.match_result import MatchCandidate

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate evaluation reports from matching results."""

    def __init__(self, sample_size: int = 50):
        self.sample_size = sample_size

    def generate(
        self,
        candidates: list[MatchCandidate],
        report_dir: str,
        run_id: str,
    ) -> str:
        """Generate an evaluation report.

        Samples pairs, computes statistics, and writes to a markdown file.
        Returns the report file path.
        """
        report_path = Path(report_dir)
        report_path.mkdir(parents=True, exist_ok=True)
        file_path = report_path / f"report_{run_id}.md"

        # Statistics
        total = len(candidates)
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        confidences: list[float] = []

        for c in candidates:
            by_type[c.match_type] = by_type.get(c.match_type, 0) + 1
            by_status[c.status] = by_status.get(c.status, 0) + 1
            confidences.append(c.confidence)

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        # Sample for manual review
        sample = random.sample(candidates, min(self.sample_size, total))

        lines = [
            f"# Matching Evaluation Report",
            f"",
            f"**Run ID:** {run_id}",
            f"**Generated:** {datetime.utcnow().isoformat()}",
            f"**Total Pairs Evaluated:** {total}",
            f"**Average Confidence:** {avg_confidence:.3f}",
            f"",
            f"## Distribution by Match Type",
            f"",
            f"| Match Type | Count | Percentage |",
            f"|---|---|---|",
        ]
        for mt, count in sorted(by_type.items()):
            pct = count / total * 100 if total > 0 else 0
            lines.append(f"| {mt} | {count} | {pct:.1f}% |")

        lines.extend([
            f"",
            f"## Distribution by Status",
            f"",
            f"| Status | Count | Percentage |",
            f"|---|---|---|",
        ])
        for st, count in sorted(by_status.items()):
            pct = count / total * 100 if total > 0 else 0
            lines.append(f"| {st} | {count} | {pct:.1f}% |")

        lines.extend([
            f"",
            f"## Sample Pairs for Manual Review ({len(sample)} pairs)",
            f"",
        ])
        for i, c in enumerate(sample, 1):
            reasons_summary = "; ".join(c.reasons.strong_evidence[:2])
            lines.extend([
                f"### Pair {i}",
                f"- **TikTok:** [{c.tiktok_item.item_id}] {c.tiktok_item.title[:80]}",
                f"- **Shopee:** [{c.shopee_item.item_id}] {c.shopee_item.title[:80]}",
                f"- **Type:** {c.match_type} | **Confidence:** {c.confidence:.3f} | **Status:** {c.status}",
                f"- **Evidence:** {reasons_summary or 'N/A'}",
                f"",
            ])

        with open(file_path, "w") as f:
            f.write("\n".join(lines))

        logger.info("Wrote evaluation report to %s", file_path)
        return str(file_path)
