# Data Quality (DQ) Thresholds

> Version: 1.0.0
> Last updated: 2026-02-25
> Status: Accepted
> Review cadence: Monthly

## Overview

This document defines the Data Quality gates that the pipeline enforces at each layer transition. DQ gates prevent bad data from propagating downstream. Each gate has a threshold, a severity level, and a defined action when the threshold is breached.

## DQ Gate Summary

| Gate ID | Check | Threshold | Layer | Severity | Action on Failure |
|---------|-------|-----------|-------|----------|-------------------|
| DQ-001 | TopN Coverage | >= 95% | Bronze -> Silver | High | Block + Alert |
| DQ-002 | Field Missing Rate (overall) | <= 5% | Silver | High | Block + Alert |
| DQ-003 | Rank Uniqueness | 100% unique per platform+category | Silver | Critical | Block |
| DQ-004 | Currency Consistency | 100% THB | Silver | Critical | Block rows |
| DQ-005 | Price Range Validity | 1 - 100,000 THB | Silver | High | Block rows |
| DQ-006 | Title Non-Empty | 100% | Silver | Critical | Block rows |
| DQ-007 | Match Score Range | [0.0, 1.0] | Match candidates | Critical | Block |
| DQ-008 | No Duplicate Matches | 0 duplicates | Match map | Critical | Block |
| DQ-009 | Insight Completeness | >= 98% | Gold | High | Warn + Alert |
| DQ-010 | Cross-Run Consistency | <= 20% change day-over-day | Gold | Medium | Warn |

## DQ-001: TopN Coverage

**Definition**: Percentage of the expected TopN products that were successfully ingested and passed to the Silver layer.

```
coverage = count(standardized_products for run_date) / (top_n * num_sub_categories * num_platforms) * 100
```

| Attribute | Value |
|-----------|-------|
| Threshold | >= 95% |
| Scope | Overall, and per (platform, sub_category) |
| Check point | After standardization, before matching |
| Severity | High |
| Action on failure | Block promotion to matching. Alert on-call. |

**Per-combination minimum**: Each (platform, sub_category) pair must have >= 90% coverage individually, even if the overall is >= 95%.

**Diagnostic output on failure**:
```
DQ-001 FAILED: Overall coverage 92.3% (target: >= 95%)
  shopee / body_wash:            95.0% (190/200) OK
  shopee / shampoo:              97.5% (195/200) OK
  shopee / skincare_moisturizer: 88.0% (176/200) FAIL
  tiktok_shop / body_wash:       93.0% (186/200) OK
  tiktok_shop / shampoo:         90.5% (181/200) OK
  tiktok_shop / skincare_moisturizer: 89.5% (179/200) FAIL
```

## DQ-002: Field Missing Rate

**Definition**: Percentage of standardized products where a required field is null, empty, or in an invalid state.

| Field | Max Missing Rate | Severity |
|-------|-----------------|----------|
| `title_cleaned` | 0% | Critical |
| `rank` | 0% | Critical |
| `platform_product_id` | 0% | Critical |
| `price_thb_satang` | 2% | High |
| `brand` | 20% | Medium |
| `review_count` | 5% | Medium |
| `rating` | 10% | Low |
| `volume_ml` or `weight_g` | 30% | Low |
| `variant` | 40% | Low |
| `image_url` | 10% | Low |

**Overall threshold**: The weighted average missing rate across all High and Critical fields must be <= 5%.

**Weighted average formula**:
```
weighted_missing = (
    missing_rate_title * 0.25 +
    missing_rate_rank * 0.25 +
    missing_rate_price * 0.20 +
    missing_rate_brand * 0.15 +
    missing_rate_review_count * 0.15
)
```

**Action on failure**:
- Critical field at any missing rate > 0%: Block entire run. Investigate immediately.
- High field exceeding threshold: Block promotion. Attempt re-extraction.
- Medium/Low fields exceeding threshold: Warn only. Allow promotion with DQ flag.

## DQ-003: Rank Uniqueness

**Definition**: Within each (platform, sub_category, run_date) partition, rank values must be unique. No two products should share the same rank.

| Attribute | Value |
|-----------|-------|
| Threshold | 100% unique (zero duplicates) |
| Scope | Per (platform, sub_category, run_date) |
| Severity | Critical |

**Check logic**:
```sql
SELECT platform, sub_category, run_date, rank, COUNT(*) as cnt
FROM standardized_products
WHERE run_date = :run_date
GROUP BY platform, sub_category, run_date, rank
HAVING cnt > 1
```

If any rows are returned, the gate fails.

**Common causes of duplicate ranks**:
- Platform returned paginated results with overlap.
- Race condition in concurrent fetching of adjacent pages.
- Platform's ranking changed during the fetch window.

**Resolution**: Deduplicate by keeping the first-fetched product for each rank. Log the discarded duplicate.

## DQ-004: Currency Consistency

**Definition**: All products in the Silver layer must have `currency = 'THB'`. Non-THB currencies indicate a data extraction or geo-routing error.

| Attribute | Value |
|-----------|-------|
| Threshold | 100% THB |
| Scope | All rows in `standardized_products` for the run_date |
| Severity | Critical |

**Action on failure**: Block non-THB rows from promotion. Investigate whether the proxy geo-location is correct (should be Thailand).

## DQ-005: Price Range Validity

**Definition**: All product prices must fall within a reasonable range for the Thai personal care market.

| Attribute | Value |
|-----------|-------|
| Minimum price | 1 THB (100 satang) |
| Maximum price | 100,000 THB (10,000,000 satang) |
| Scope | All rows with non-null `price_thb_satang` |
| Severity | High |

**Rationale for range**:
- Minimum 1 THB: Below this is almost certainly a parsing error (e.g., extracting "0" or a partial number).
- Maximum 100,000 THB: Premium skincare products can be expensive, but anything above this for personal_care is likely a data error or a bundled/wholesale listing.

**Action on failure**: Block individual rows outside the range. Do not block the entire run.

**Diagnostic categories**:
```
Price < 1 THB:       Likely parse error (check raw_price extraction)
Price 1-10 THB:      Suspicious for personal care (flag for review)
Price 10-10,000 THB: Normal range
Price 10K-100K THB:  Premium/luxury segment (flag but allow)
Price > 100K THB:    Likely error (block)
```

## DQ-006: Title Non-Empty

**Definition**: Every standardized product must have a non-empty `title_cleaned` field.

| Attribute | Value |
|-----------|-------|
| Threshold | 100% non-empty |
| Non-empty definition | `title_cleaned IS NOT NULL AND LENGTH(TRIM(title_cleaned)) > 0` |
| Severity | Critical |

Products without titles cannot be meaningfully matched or displayed. They are blocked during standardization and recorded as extraction failures.

## DQ-007: Match Score Range

**Definition**: All composite and individual signal scores in `match_candidates` must be within the valid range [0.0, 1.0].

| Attribute | Value |
|-----------|-------|
| Threshold | 100% within [0.0, 1.0] |
| Fields checked | `composite_score`, `brand_score`, `spec_score`, `title_score`, `price_score` |
| Severity | Critical |

A score outside this range indicates a bug in the scoring logic. Block the matching output and investigate.

## DQ-008: No Duplicate Matches

**Definition**: The `match_map` must not contain duplicate active matches for the same product.

**Rules**:
- A Shopee product can be actively matched to at most one TikTok product (and vice versa) per run_date.
- Multiple `match_type` entries for the same pair are not allowed.
- Historical/superseded matches (`is_active = false`) are excluded from this check.

```sql
SELECT product_id_shopee, COUNT(*) as cnt
FROM match_map
WHERE run_date = :run_date AND is_active = true
GROUP BY product_id_shopee
HAVING cnt > 1
```

**Severity**: Critical. Duplicate matches would cause incorrect cross-platform insights.

## DQ-009: Insight Completeness

**Definition**: Percentage of standardized products that have corresponding entries in `insights_daily` for all 3 window sizes.

```
completeness = count(insights_daily for run_date) / (count(standardized_products for run_date) * 3) * 100
```

| Attribute | Value |
|-----------|-------|
| Threshold | >= 98% |
| Severity | High |

**Common causes of incomplete insights**:
- Products entered TopN for the first time (no historical data for delta computation). These should still have insights rows with null deltas.
- Edge cases in window calculation (product existed 13 days ago but not 14).

## DQ-010: Cross-Run Consistency

**Definition**: The day-over-day change in key aggregate metrics should not exceed reasonable bounds, unless a market event explains the shift.

| Metric | Maximum Day-over-Day Change |
|--------|-----------------------------|
| Total product count per platform | +/- 20% |
| Average price per sub-category | +/- 15% |
| Match rate (% of products matched) | +/- 15 percentage points |
| Brand distribution (top-5 brand share) | +/- 10 percentage points |

| Attribute | Value |
|-----------|-------|
| Severity | Medium |
| Action | Warn. Log anomaly. Do not block. |

This is a soft gate. Violations are logged and surfaced in the anomaly dashboard but do not block data promotion. See [alerts-anomaly runbook](../runbooks/alerts-anomaly.md) for investigation procedures.

## DQ Report Format

Every pipeline run produces a DQ report with the following structure:

```json
{
  "run_id": "shopee_personal_care_2026-02-25",
  "run_date": "2026-02-25",
  "overall_status": "PASS",
  "gates": [
    {
      "gate_id": "DQ-001",
      "name": "TopN Coverage",
      "status": "PASS",
      "value": 97.2,
      "threshold": 95.0,
      "details": { ... }
    },
    {
      "gate_id": "DQ-002",
      "name": "Field Missing Rate",
      "status": "WARN",
      "value": 4.8,
      "threshold": 5.0,
      "details": { "brand_missing": 18.5, "price_missing": 0.5, ... }
    }
  ],
  "blocked_rows": 3,
  "total_rows": 1200,
  "computed_at": "2026-02-25T03:45:00Z"
}
```

## Threshold Tuning Process

DQ thresholds are reviewed monthly alongside SLO review:

1. Analyze DQ gate pass/fail rates over the past 30 days.
2. Identify gates that are too tight (frequent false blocks) or too loose (letting bad data through).
3. Propose threshold adjustments with supporting data.
4. Review and approve changes.
5. Update this document and bump `rule_version`.

## Related Documents

- [slo-thresholds.md](slo-thresholds.md) - SLO definitions that depend on DQ gates
- [e2e-test-cases.md](e2e-test-cases.md) - E2E tests for DQ gate validation (TC-006)
- [../runbooks/field-missing-spike.md](../runbooks/field-missing-spike.md) - Handling field missing spikes
- [../design/data-model.md](../design/data-model.md) - Table definitions and field types
