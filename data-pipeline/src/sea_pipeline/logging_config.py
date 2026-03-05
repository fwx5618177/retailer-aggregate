"""JSON structured logging setup for the SEA data pipeline."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def __init__(
        self,
        run_id: str = "",
        batch_id: str = "",
        platform: str = "",
        category: str = "",
        event_date: str = "",
    ) -> None:
        super().__init__()
        self.run_id = run_id
        self.batch_id = batch_id
        self.platform = platform
        self.category = category
        self.event_date = event_date

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "run_id": getattr(record, "run_id", self.run_id),
            "batch_id": getattr(record, "batch_id", self.batch_id),
            "platform": getattr(record, "platform", self.platform),
            "category": getattr(record, "category", self.category),
            "event_date": getattr(record, "event_date", self.event_date),
        }

        if record.exc_info and record.exc_info[1] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        extra_keys = {
            k: v
            for k, v in record.__dict__.items()
            if k not in logging.LogRecord("", 0, "", 0, None, None, None).__dict__
            and k not in log_entry
        }
        if extra_keys:
            log_entry["extra"] = extra_keys

        return json.dumps(log_entry, ensure_ascii=False, default=str)


def setup_logging(
    level: int = logging.INFO,
    run_id: str = "",
    batch_id: str = "",
    platform: str = "",
    category: str = "",
    event_date: str = "",
) -> logging.Logger:
    """Configure and return the pipeline root logger with JSON formatting.

    Parameters
    ----------
    level:
        Python logging level (default INFO).
    run_id / batch_id / platform / category / event_date:
        Context fields that are stamped on every log line.

    Returns
    -------
    logging.Logger
        The configured ``sea_pipeline`` logger.
    """
    logger = logging.getLogger("sea_pipeline")
    logger.setLevel(level)

    # Avoid duplicate handlers when called more than once
    if logger.handlers:
        logger.handlers.clear()

    formatter = JSONFormatter(
        run_id=run_id,
        batch_id=batch_id,
        platform=platform,
        category=category,
        event_date=event_date,
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.propagate = False

    return logger
