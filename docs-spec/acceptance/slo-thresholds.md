# Service Level Objectives (SLOs)

> Version: 1.0.0
> Last updated: 2026-02-25
> Status: Accepted
> Review cadence: Monthly

## Overview

This document defines the Service Level Objectives for the SEA Retailer Intelligence Platform. SLOs set the target reliability and performance for each component. They are not contractual guarantees (those would be SLAs) but internal targets that guide operational decisions.

## SLO Summary

| SLO ID | Metric | Target | Measurement Window |
|--------|--------|--------|--------------------|
| SLO-001 | Data Freshness | T+2h | Per daily run |
| SLO-002 | API Latency (P95) | < 1 second | Rolling 24 hours |
| SLO-003 | Daily Pipeline Success Rate | >= 99% | Rolling 30 days |
| SLO-004 | Field Missing Rate | < 5% | Per daily run |
| SLO-005 | API Availability | >= 99.5% | Rolling 30 days |
| SLO-006 | Review Queue Latency | < 24 hours | Rolling 7 days |
| SLO-007 | TopN Coverage | >= 95% | Per daily run |

## SLO-001: Data Freshness

**Definition**: Time elapsed from the scheduled pipeline start time to the moment serving data (Gold layer) is available for API queries.

| Attribute | Value |
|-----------|-------|
| Target | <= 2 hours (T+2h) |
| Measurement | `serving_available_at - scheduled_start_time` |
| Scheduled start | 02:00 UTC+7 daily |
| Target available by | 04:00 UTC+7 daily |

**Breakdown of expected timing**:

| Phase | Expected Duration |
|-------|-------------------|
| Ingestion (both platforms) | 60 minutes |
| Standardization | 10 minutes |
| Matching | 10 minutes |
| Insights computation | 10 minutes |
| Buffer | 30 minutes |
| **Total** | **120 minutes (2 hours)** |

**Measurement method**:
- The pipeline records `pipeline_start_time` at the beginning of ingestion.
- The insights module records `serving_promoted_at` when the Gold snapshot is marked as `current`.
- Freshness = `serving_promoted_at - scheduled_start_time`.

**Alert thresholds**:
- Warning: Freshness > 2 hours.
- Critical: Freshness > 4 hours.
- Escalation: Freshness > 6 hours -> page on-call engineer.

**Error budget**: Over a 30-day rolling window, the pipeline may exceed the 2-hour freshness target on at most 1 day (96.7% compliance).

## SLO-002: API Latency

**Definition**: The 95th percentile (P95) response time for all API read endpoints, measured at the server side (excluding network transit to the client).

| Attribute | Value |
|-----------|-------|
| Target | P95 < 1 second |
| Scope | All GET endpoints |
| Measurement | Server-side response time (from request received to response sent) |
| Excluded | POST `/pipeline/trigger` (async operation, returns immediately) |

**Per-endpoint latency budgets**:

| Endpoint | P50 Target | P95 Target | P99 Target |
|----------|-----------|-----------|-----------|
| GET `/insights/rankings` | < 200ms | < 500ms | < 1s |
| GET `/insights/movers` | < 200ms | < 500ms | < 1s |
| GET `/insights/cross-platform` | < 300ms | < 700ms | < 1.5s |
| GET `/products/{platform}/{id}` | < 100ms | < 300ms | < 500ms |
| GET `/review-queue` | < 200ms | < 500ms | < 1s |

**Measurement method**:
- FastAPI middleware records request start and end times.
- Latency metrics are emitted per endpoint per minute.
- P50, P95, P99 are computed over rolling 5-minute windows.

**Alert thresholds**:
- Warning: P95 > 1 second for 5 consecutive minutes.
- Critical: P95 > 2 seconds for 5 consecutive minutes.

## SLO-003: Daily Pipeline Success Rate

**Definition**: Percentage of daily pipeline runs that complete successfully (all modules finish without fatal errors) over a rolling 30-day window.

| Attribute | Value |
|-----------|-------|
| Target | >= 99% (at most 1 failed day per 30 days) |
| Definition of success | Pipeline run manifest status = `completed` AND all DQ gates pass |
| Definition of failure | Pipeline run manifest status = `failed` OR a DQ gate blocks promotion |
| Measurement window | Rolling 30 days |

**Notes**:
- A run that completes in `degraded` mode (some products stubbed) counts as successful if overall DQ gates pass.
- A manually triggered re-run that succeeds does NOT count as a failure for the original scheduled run if the re-run completes within the same calendar day.

**Alert thresholds**:
- Warning: 2 failures in 30 days.
- Critical: 3 failures in 30 days.

## SLO-004: Field Missing Rate

**Definition**: Percentage of products in the Silver layer (standardized_products) where a required field is null or empty, averaged across all required fields.

| Attribute | Value |
|-----------|-------|
| Target | < 5% overall |
| Scope | All products in `standardized_products` for a given run_date |
| Required fields | `title_cleaned`, `price_thb_satang`, `brand`, `review_count`, `rank` |

**Per-field targets**:

| Field | Missing Rate Target | Severity if Breached |
|-------|--------------------|--------------------|
| `title_cleaned` | 0% | Critical (blocks promotion) |
| `rank` | 0% | Critical (blocks promotion) |
| `price_thb_satang` | < 2% | High |
| `brand` | < 20% | Medium |
| `review_count` | < 5% | Medium |
| `rating` | < 10% | Low |
| `volume_ml` / `weight_g` | < 30% | Low |

**Measurement method**:
- The standardization module computes field completeness as a post-processing step.
- Results are logged in the DQ report and compared against these thresholds.

**Alert thresholds**:
- Warning: Any field exceeds its per-field target.
- Critical: Overall missing rate exceeds 5% or a Critical-severity field has any missing values.

## SLO-005: API Availability

**Definition**: Percentage of time the API is able to serve requests successfully (HTTP 2xx or expected 4xx for client errors), excluding planned maintenance.

| Attribute | Value |
|-----------|-------|
| Target | >= 99.5% |
| Measurement | `(total_minutes - downtime_minutes) / total_minutes` over rolling 30 days |
| Downtime definition | API returns 5xx for > 50% of requests in a 1-minute window |

**Error budget**: 30 days x 24 hours x 60 minutes = 43,200 minutes. 0.5% error budget = 216 minutes (~3.6 hours) of allowed downtime per 30-day window.

## SLO-006: Review Queue Latency

**Definition**: Average time from a match candidate being enqueued in the review queue to a decision (approve/reject/defer) being made.

| Attribute | Value |
|-----------|-------|
| Target | < 24 hours average |
| Measurement window | Rolling 7 days |
| Measurement | Average of `reviewed_at - created_at` for all items resolved in the window |

**Alert thresholds**:
- Warning: Average review latency > 24 hours.
- Critical: Average review latency > 48 hours.
- See [review-backlog runbook](../runbooks/review-backlog.md) for response procedures.

## SLO-007: TopN Coverage

**Definition**: Percentage of expected TopN products successfully ingested and standardized, per platform per sub-category.

| Attribute | Value |
|-----------|-------|
| Target | >= 95% |
| Expected products | `top_n` setting x number of sub-categories x number of platforms |
| Successfully processed | Products in `standardized_products` with `fetch_status != fetch_failed` |

**Measurement method**:
- Coverage = `count(standardized_products where run_date=X) / expected_total * 100%`
- Computed per platform, per sub-category, and overall.

**Alert thresholds**:
- Warning: Coverage < 95% for any platform+sub_category combination.
- Critical: Coverage < 90% for any combination OR overall coverage < 95%.

## SLO Dashboard

All SLO metrics are displayed on the operational dashboard with:
- Current value vs target.
- Trend over the last 30 days.
- Remaining error budget.
- Time since last breach.

## SLO Review Process

SLOs are reviewed monthly:

1. Analyze SLO compliance over the past 30 days.
2. Identify any breaches and their root causes.
3. Determine if targets need adjustment (tighter or looser based on actual performance).
4. Update this document if targets change (with changelog entry).

## Related Documents

- [dq-thresholds.md](dq-thresholds.md) - Detailed data quality thresholds
- [e2e-test-cases.md](e2e-test-cases.md) - E2E tests that validate SLO compliance
- [../runbooks/alerts-anomaly.md](../runbooks/alerts-anomaly.md) - Anomaly handling when SLOs are breached
