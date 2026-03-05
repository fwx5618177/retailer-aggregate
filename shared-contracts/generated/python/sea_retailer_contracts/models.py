"""Shared Pydantic models for SEA Retailer Top Selling Intelligence."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from sea_retailer_contracts.enums import (
    AlertStatus,
    AlertType,
    DQStatus,
    MatchStatus,
    MatchType,
    OurStatus,
    Platform,
    ProxyType,
    Severity,
)


class TopItem(BaseModel):
    event_date: date
    platform: Platform
    item_id: str
    title: str
    category: str
    rank: int = Field(ge=1)
    url: str | None = None
    brand_raw: str | None = None
    brand_std: str | None = None
    size_value: float | None = None
    size_unit: str | None = None
    pack_count: int | None = Field(default=None, ge=1)
    image_url: str | None = None
    ingested_at: datetime | None = None
    source_url: str | None = None
    source_type: str | None = None
    batch_id: str | None = None
    schema_version: str = "1.0.0"


class PriceSnapshot(BaseModel):
    event_date: date
    platform: Platform
    item_id: str
    list_price: int = Field(ge=0, description="Price in smallest currency unit")
    promo_price: int | None = Field(default=None, ge=0)
    promo_flag: bool = False
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    ingested_at: datetime | None = None
    batch_id: str | None = None
    schema_version: str = "1.0.0"


class SalesProxy(BaseModel):
    event_date: date
    platform: Platform
    item_id: str
    proxy_type: ProxyType
    proxy_value: str
    proxy_numeric: float | None = None
    ingested_at: datetime | None = None
    batch_id: str | None = None
    schema_version: str = "1.0.0"


class FieldAlignment(BaseModel):
    brand_match: bool = False
    brand_a: str | None = None
    brand_b: str | None = None
    spec_match: bool = False
    spec_a: str | None = None
    spec_b: str | None = None
    title_similarity: float = 0.0
    price_band_match: bool = False


class MatchReasons(BaseModel):
    strong_evidence: list[str] = Field(default_factory=list)
    weak_evidence: list[str] = Field(default_factory=list)
    field_alignment: FieldAlignment = Field(default_factory=FieldAlignment)
    missing_fields: list[str] = Field(default_factory=list)


class MatchMapPlatform(BaseModel):
    tiktok_item_id: str
    shopee_item_id: str
    match_type: MatchType
    confidence: float = Field(ge=0, le=1)
    status: MatchStatus
    reasons: MatchReasons = Field(default_factory=MatchReasons)
    rule_version: str | None = None
    model_version: str | None = None
    ingested_at: datetime | None = None
    batch_id: str | None = None
    schema_version: str = "1.0.0"


class OurMapping(BaseModel):
    platform: Platform
    item_id: str
    our_status: OurStatus
    our_sku_id: str | None = None
    notes: str | None = None
    updated_by: str | None = None
    updated_at: datetime | None = None
    schema_version: str = "1.0.0"


class AlertReasons(BaseModel):
    trigger_metric: str | None = None
    old_value: str | float | None = None
    new_value: str | float | None = None
    threshold: str | float | None = None
    context: str | None = None


class Alert(BaseModel):
    alert_id: str
    event_date: date
    platform: Platform | None = None
    item_ids: list[str] = Field(default_factory=list)
    alert_type: AlertType
    severity: Severity
    status: AlertStatus = AlertStatus.OPEN
    title: str
    description: str | None = None
    reasons: AlertReasons = Field(default_factory=AlertReasons)
    suggested_action: str | None = None
    batch_id: str | None = None
    schema_version: str = "1.0.0"


class DQResult(BaseModel):
    check_name: str
    passed: bool
    actual_value: float
    threshold: float
    message: str


class RunManifest(BaseModel):
    run_id: str
    batch_id: str
    schema_version: str = "1.0.0"
    rule_version: str | None = None
    model_version: str | None = None
    created_at: datetime
    parameters: dict[str, Any] = Field(default_factory=dict)
    row_counts: dict[str, int] = Field(default_factory=dict)
    dq_results: list[DQResult] = Field(default_factory=list)
    dq_status: DQStatus = DQStatus.PASSED
    duration_seconds: float | None = None
