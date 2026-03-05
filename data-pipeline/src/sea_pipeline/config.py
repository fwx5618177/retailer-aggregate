"""Configuration loader for the SEA data pipeline.

Reads YAML files, supports config override (merge), and provides
a PipelineConfig pydantic model. Environment variables with the SEA_ prefix
override any YAML-level setting using double-underscore nesting
(e.g. SEA_INGESTION__USE_STUB=true).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pydantic sub-models
# ---------------------------------------------------------------------------

class ScopeConfig(BaseModel):
    platforms: list[str] = Field(default_factory=lambda: ["shopee", "tiktok"])
    categories: list[str] = Field(default_factory=lambda: ["personal_care"])
    sites: list[str] = Field(default_factory=lambda: ["th"])
    top_n: int = 200
    window_days: int = 14


class RateLimitConfig(BaseModel):
    requests_per_second: float = 2.0
    max_concurrent: int = 3
    backoff_factor: float = 2.0
    max_retries: int = 3


class PlatformEndpointConfig(BaseModel):
    base_url: str = ""
    search_endpoint: str = ""
    detail_endpoint: str = ""
    timeout: int = 30


class IngestionConfig(BaseModel):
    use_stub: bool = False
    stub_fallback: bool = True
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    shopee: PlatformEndpointConfig = Field(default_factory=PlatformEndpointConfig)
    tiktok: PlatformEndpointConfig = Field(default_factory=PlatformEndpointConfig)


class StandardisationConfig(BaseModel):
    brand_dictionary_path: str = "data/brand_dictionary.yaml"
    unit_rules_path: str = "data/unit_rules.yaml"
    spec_tolerance_pct: float = 10.0


class PriceRangeConfig(BaseModel):
    min: int = 100
    max: int = 10_000_000


class DQConfig(BaseModel):
    mode: str = "block"
    topn_coverage_min: float = 0.95
    field_missing_rate_max: float = 0.05
    rank_uniqueness: bool = True
    currency_consistency: bool = True
    price_range: PriceRangeConfig = Field(default_factory=PriceRangeConfig)


class StorageConfig(BaseModel):
    mode: str = "local"
    duckdb_path: str = "data/pipeline.duckdb"


class ExportConfig(BaseModel):
    serving_dir: str = "data/serving"
    format: str = "parquet"


class PipelineConfig(BaseModel):
    scope: ScopeConfig = Field(default_factory=ScopeConfig)
    ingestion: IngestionConfig = Field(default_factory=IngestionConfig)
    standardisation: StandardisationConfig = Field(default_factory=StandardisationConfig)
    dq: DQConfig = Field(default_factory=DQConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into *base* (mutates base)."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def _apply_env_overrides(data: dict[str, Any], prefix: str = "SEA_") -> dict[str, Any]:
    """Override config values from environment variables.

    Variables are expected in the form ``SEA_<SECTION>__<KEY>=value`` where
    double-underscore separates nesting levels.  Values are coerced to bool /
    int / float where possible.
    """
    for env_key, env_val in os.environ.items():
        if not env_key.startswith(prefix):
            continue
        parts = env_key[len(prefix):].lower().split("__")
        target = data
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        coerced = _coerce(env_val)
        target[parts[-1]] = coerced
    return data


def _coerce(value: str) -> Any:
    """Best-effort coerce a string to a primitive Python type."""
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file and return its content as a dictionary."""
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_config(
    config_path: str | Path,
    override_path: str | Path | None = None,
) -> PipelineConfig:
    """Load pipeline configuration from YAML with optional override and env vars.

    Parameters
    ----------
    config_path:
        Path to the base YAML configuration file.
    override_path:
        Optional path to an override YAML that is deep-merged on top.

    Returns
    -------
    PipelineConfig
        A fully validated pydantic model.
    """
    data = load_yaml(config_path)

    if override_path is not None:
        override_data = load_yaml(override_path)
        data = _deep_merge(data, override_data)

    data = _apply_env_overrides(data)

    return PipelineConfig(**data)
