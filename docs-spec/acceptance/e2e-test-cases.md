# End-to-End Test Cases

> Version: 1.0.0
> Last updated: 2026-02-25
> Status: Accepted

## Overview

This document defines the end-to-end test cases that validate the complete pipeline from ingestion through to API serving. Each test case specifies the objective, preconditions, steps, and expected outcomes. These tests should pass before any release.

## Test Environment

| Attribute | Value |
|-----------|-------|
| Data source | Fixture data (static HTML/JSON files mimicking platform responses) |
| Storage | Local DuckDB |
| API | FastAPI dev server |
| Fixture size | 20 products per platform per sub-category (reduced TopN for test speed) |

## TC-001: Pipeline Produces Serving Data

**Objective**: Verify that a complete pipeline run transforms raw fixture data into queryable Gold-layer serving data.

**Preconditions**:
- Fixture data available in `tests/fixtures/raw/` for Shopee and TikTok Shop.
- No existing data in the local DuckDB for the test run_date.
- Pipeline config set to test values (top_n=20, fixture data source).

**Steps**:
1. Trigger a full pipeline run for run_date `2026-01-15` using fixture data.
2. Wait for pipeline completion.
3. Query `insights_daily` table for run_date `2026-01-15`.

**Expected outcomes**:
- Pipeline exits with status code 0.
- Run manifest shows `status: completed` with no errors.
- `raw_listings` contains 120 rows (20 products x 3 sub-categories x 2 platforms).
- `standardized_products` contains 120 rows with all mandatory fields populated.
- `insights_daily` contains 360 rows (120 products x 3 window sizes).
- All rows in `insights_daily` have `run_date = 2026-01-15`.
- `schema_version` and `rule_version` are populated on all rows.

**Pass criteria**: All expected outcomes met.

## TC-002: Matching Produces Match Map

**Objective**: Verify that the matching module produces correct cross-platform match results.

**Preconditions**:
- Fixture data includes 5 known matching pairs (same product on both platforms) with pre-determined expected match types.
- Fixture data includes 3 known non-matching products (present on only one platform).

**Steps**:
1. Run pipeline through the matching module.
2. Query `match_candidates` table for scored pairs.
3. Query `match_map` table for accepted matches.
4. Verify known matching pairs.

**Expected outcomes**:
- `match_candidates` contains scored pairs for all cross-platform comparisons within the same brand+category blocks.
- All 5 known matching pairs appear in `match_candidates` with `composite_score > 0.65`.
- At least 3 of the 5 known pairs are auto-accepted (`composite_score >= 0.85`) and appear in `match_map`.
- The 3 known non-matching products do not appear as accepted matches in `match_map`.
- Each `match_candidates` row has a populated `reasons` JSON with all 4 signal scores.
- `match_map` rows have `source: auto_approved` and valid `match_type`.

**Known matching pairs in fixture data**:

| Pair | Shopee Product | TikTok Product | Expected Match Type |
|------|---------------|----------------|---------------------|
| 1 | NIVEA Body Wash Extra White 500ml | NIVEA Extra White Body Wash 500ml | `exact_same` |
| 2 | Pantene Shampoo Silky Smooth 400ml | Pantene Silky Smooth Care Shampoo 400ml | `exact_same` |
| 3 | NIVEA Body Wash Extra White 500ml | NIVEA Extra White Body Wash 200ml | `variant_family` |
| 4 | Dove Deeply Nourishing Body Wash 400ml | Dove Nourishing Body Wash 400ml | `exact_same` |
| 5 | Cetaphil Gentle Skin Cleanser 500ml | Cetaphil Gentle Cleanser 500ml | `exact_same` |

**Pass criteria**: All known pairs correctly identified; no false positives for non-matching products.

## TC-003: API Serves Data Correctly

**Objective**: Verify that all 7 API endpoints return correct data from the Gold layer.

**Preconditions**:
- Pipeline has completed for run_date `2026-01-15` with fixture data.
- FastAPI server is running.
- API key with `admin` role is configured.

**Steps and expected outcomes**:

### TC-003a: GET `/insights/rankings`
- Request: `GET /api/v1/insights/rankings?platform=shopee&sub_category=body_wash&window_days=14`
- Expected: 200 OK, response contains 20 products sorted by `current_rank` ASC, all from Shopee body_wash.
- Verify: Pagination works (request with `limit=5`, check `has_more=true`, follow cursor).

### TC-003b: GET `/insights/movers`
- Request: `GET /api/v1/insights/movers?direction=up&limit=10`
- Expected: 200 OK, response contains up to 10 products with positive `rank_delta`, sorted by `rank_delta` DESC.

### TC-003c: GET `/insights/cross-platform`
- Request: `GET /api/v1/insights/cross-platform?match_type=exact_same`
- Expected: 200 OK, response contains matched product pairs with both platforms' data and `cross_platform_price_gap`.

### TC-003d: GET `/products/{platform}/{product_id}`
- Request: `GET /api/v1/products/shopee/{known_product_id}?window_days=14`
- Expected: 200 OK, response contains product detail with rank history, price history, and match info.

### TC-003e: GET `/review-queue`
- Request: `GET /api/v1/review-queue?status=pending`
- Expected: 200 OK, response contains pending review items with reasons and suggested match types.

### TC-003f: POST `/review-queue/{review_id}/decision`
- Request: POST with `{"action": "approve", "match_type": "exact_same", "reason": "Test approval"}`
- Expected: 200 OK, review item status updated to `approved`. Match appears in `match_map` with `source: human_review`.

### TC-003g: POST `/pipeline/trigger`
- Request: POST with `{"run_date": "2026-01-16", "top_n": 20}`
- Expected: 202 Accepted, response contains `run_id` and `progress_url`.

**Pass criteria**: All sub-tests return expected status codes and data shapes.

## TC-004: Review Workflow End-to-End

**Objective**: Verify the complete review lifecycle from enqueue through decision to match_map update.

**Preconditions**:
- Pipeline has produced review_queue items (at least 2 items in `pending` status).
- Reviewer API key available.

**Steps**:
1. List pending review items: `GET /api/v1/review-queue?status=pending`
2. Note the first item's `review_id` and examine its `reasons`.
3. Approve the first item: `POST /api/v1/review-queue/{review_id}/decision` with `{"action": "approve", "match_type": "variant_family"}`.
4. Reject the second item: `POST /api/v1/review-queue/{review_id}/decision` with `{"action": "reject", "reason": "Different product type"}`.
5. Query match_map for the approved pair.
6. Query match_map for the rejected pair.

**Expected outcomes**:
- Step 1: Returns at least 2 items with `status: pending`.
- Step 3: Returns updated item with `status: approved`, `decision_match_type: variant_family`.
- Step 4: Returns updated item with `status: rejected`.
- Step 5: Approved pair appears in `match_map` with `source: human_review`, `match_type: variant_family`.
- Step 6: Rejected pair does NOT appear in `match_map`.
- Both decisions are recorded in the audit trail.

**Pass criteria**: All lifecycle states transition correctly; match_map is updated only for approvals.

## TC-005: Audit Trail Verification

**Objective**: Verify that all write operations produce audit trail entries.

**Preconditions**:
- Pipeline has run and at least one review decision has been made.

**Steps**:
1. Trigger a pipeline run (creates audit entry for `pipeline_trigger`).
2. Approve a review item (creates audit entry for `review_approve`).
3. Query the audit trail for all entries from this test session.

**Expected outcomes**:
- Audit trail contains an entry for the pipeline trigger with:
  - `action: pipeline_trigger`
  - `user_id` matching the API key owner
  - `resource_type: pipeline_run`
  - `request_body` containing the trigger parameters
  - `response_status: 202`
- Audit trail contains an entry for the review approval with:
  - `action: review_approve`
  - `user_id` matching the reviewer
  - `resource_type: review_queue`
  - `resource_id` matching the review_id
- All audit entries have valid `audit_id`, `timestamp`, and `request_id`.
- Audit entries are immutable (no UPDATE/DELETE operations succeed).

**Pass criteria**: All write operations have corresponding audit entries with complete metadata.

## TC-006: Data Quality Gates Block Bad Data

**Objective**: Verify that DQ gates prevent invalid data from reaching the Gold layer.

**Preconditions**:
- Fixture data includes intentionally bad records: 2 products with missing titles, 1 with price=0, 1 with currency=USD.

**Steps**:
1. Run pipeline with the bad fixture data.
2. Check standardization DQ report.
3. Query `standardized_products` for the bad records.
4. Query `insights_daily` for the bad records.

**Expected outcomes**:
- DQ report flags the 4 bad records.
- Products with missing titles are not present in `standardized_products` (blocked).
- Product with price=0 is not present in `standardized_products` (blocked).
- Product with currency=USD is not present in `standardized_products` (blocked).
- None of the blocked products appear in `insights_daily`.
- Pipeline completes successfully (bad records are logged and skipped, not pipeline-fatal).
- Run manifest records the blocked products count.

**Pass criteria**: All DQ violations are caught; bad data does not reach Gold layer.

## TC-007: Idempotent Pipeline Rerun

**Objective**: Verify that running the pipeline twice for the same date produces identical results.

**Preconditions**:
- First pipeline run completed for run_date `2026-01-15`.

**Steps**:
1. Record row counts and checksums for all tables after the first run.
2. Run the pipeline again for the same run_date `2026-01-15`.
3. Record row counts and checksums for all tables after the second run.

**Expected outcomes**:
- Row counts are identical between first and second runs.
- Data checksums are identical (excluding `fetched_at`, `standardized_at`, `computed_at` timestamps).
- No duplicate rows in any table.
- Run manifest shows a second `execution_id` but the same `run_id`.

**Pass criteria**: Pipeline is fully idempotent.

## TC-008: RBAC Enforcement

**Objective**: Verify that API endpoints enforce role-based access control.

**Steps**:
1. With `viewer` API key: `GET /api/v1/insights/rankings` -> expected 200.
2. With `viewer` API key: `POST /api/v1/review-queue/{id}/decision` -> expected 403.
3. With `viewer` API key: `POST /api/v1/pipeline/trigger` -> expected 403.
4. With `reviewer` API key: `POST /api/v1/review-queue/{id}/decision` -> expected 200.
5. With `reviewer` API key: `POST /api/v1/pipeline/trigger` -> expected 403.
6. With `operator` API key: `POST /api/v1/pipeline/trigger` -> expected 202.
7. With invalid API key: any endpoint -> expected 401.

**Pass criteria**: All role-permission combinations enforced correctly.

## Test Execution

```bash
# Run all E2E tests
python -m pytest tests/e2e/ -v --tb=long

# Run a specific test case
python -m pytest tests/e2e/test_pipeline.py::test_tc001_pipeline_produces_serving_data -v
```

## Related Documents

- [slo-thresholds.md](slo-thresholds.md) - SLO targets that E2E tests validate
- [dq-thresholds.md](dq-thresholds.md) - DQ thresholds enforced in TC-006
- [../design/api-design.md](../design/api-design.md) - API specification for TC-003 and TC-008
