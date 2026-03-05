"""DQ gate -- decides whether the pipeline should proceed after checks."""

from __future__ import annotations

import logging
from enum import Enum

from sea_pipeline.dq.checks import DQResult

logger = logging.getLogger("sea_pipeline")


class DQStatus(str, Enum):
    PASSED = "PASSED"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


class DQGate:
    """Evaluate DQ results against a gating policy.

    Modes
    -----
    block
        Any failed check causes the overall status to be FAILED.
    degrade
        Any failed check causes DEGRADED (pipeline continues but data is flagged).
    warn
        Always PASSED; failures are logged as warnings only.
    """

    def evaluate(
        self,
        results: list[DQResult],
        mode: str = "block",
    ) -> tuple[DQStatus, list[DQResult]]:
        """Evaluate the list of DQ results and return the overall status.

        Parameters
        ----------
        results:
            Individual check results.
        mode:
            One of ``"block"``, ``"degrade"``, or ``"warn"``.

        Returns
        -------
        tuple[DQStatus, list[DQResult]]
            The overall status and the (unchanged) list of results.
        """
        failures = [r for r in results if not r.passed]

        if not failures:
            logger.info("DQ gate: all %d checks passed.", len(results))
            return DQStatus.PASSED, results

        for f in failures:
            logger.warning("DQ check failed: %s -- %s", f.check_name, f.message)

        if mode == "block":
            logger.error(
                "DQ gate BLOCKED: %d/%d checks failed.", len(failures), len(results),
            )
            return DQStatus.FAILED, results

        if mode == "degrade":
            logger.warning(
                "DQ gate DEGRADED: %d/%d checks failed.", len(failures), len(results),
            )
            return DQStatus.DEGRADED, results

        # mode == "warn" (or anything else)
        logger.warning(
            "DQ gate WARN: %d/%d checks failed (proceeding anyway).",
            len(failures),
            len(results),
        )
        return DQStatus.PASSED, results
