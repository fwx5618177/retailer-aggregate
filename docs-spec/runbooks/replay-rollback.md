# Runbook: Data Replay and Rollback

> Severity: Reference (used by other runbooks)
> Module: All pipeline modules
> Last updated: 2026-02-25
> On-call team: Data Engineering

## Overview

This runbook describes how to replay (rerun) parts of the pipeline and how to rollback serving data to a previous known-good state. These are foundational procedures referenced by all other runbooks.

## Key Concepts

### Run Identity

Every pipeline execution is identified by:
- **`run_id`**: Format `{platform}_{category}_{run_date}` (e.g., `shopee_personal_care_2026-02-25`). Uniquely identifies what data was processed.
- **`run_date`**: The target date for the data (not necessarily when the pipeline actually ran).
- **`execution_id`**: UUID generated per execution attempt. Multiple executions can share the same `run_id` (replays).

### Idempotent Writes

All pipeline writes are idempotent based on `run_id`:
- Bronze: `raw_id = {platform}_{product_id}_{run_date}` -- same fetch overwrites same row.
- Silver: `std_id = {platform}_{product_id}_{run_date}` -- same standardization overwrites.
- Silver: `candidate_id = {std_id_a}_{std_id_b}` -- same matching pair overwrites.
- Gold: `insight_id = {platform}_{product_id}_{run_date}_{window}` -- same insight overwrites.

This means replaying with the same `run_id` safely overwrites previous output without creating duplicates.

### Versioned Configuration

Pipeline behavior is governed by versioned config files:

| Config | Version Key | Location |
|--------|-------------|----------|
| Extraction rules | `rule_version` | `config/extraction_rules/*.yaml` |
| Matching thresholds | `matching_rule_version` | `config/matching_config.yaml` |
| Brand aliases | `brand_dict_version` | `config/brand_aliases.yaml` |
| Insights parameters | `insights_rule_version` | `config/insights_config.yaml` |

All config versions are recorded in each output row, enabling traceability.

## Replay Procedures

### Replay: Full Pipeline (from Ingestion)

Re-fetches data from source platforms and re-processes everything. Use when raw data is suspected to be bad.

```bash
python -m pipeline.cli replay --run-date 2026-02-25 \
  --start-from ingestion \
  --platforms shopee,tiktok_shop \
  --sub-categories body_wash,shampoo,skincare_moisturizer
```

**What happens**:
1. Ingestion re-fetches all TopN products from both platforms.
2. New raw data overwrites Bronze layer for this run_date.
3. Standardization, Matching, and Insights re-run on the new raw data.
4. Gold serving layer is updated with new insights.

**Duration**: ~90 minutes (limited by fetch rate).

**Caution**: This sends fresh requests to platforms. Respect rate limits. Do not replay full pipeline more than 2x per day per platform.

### Replay: From Standardization

Re-processes existing raw data with updated extraction rules. Use when selectors were fixed.

```bash
python -m pipeline.cli replay --run-date 2026-02-25 \
  --start-from standardization
```

**What happens**:
1. Reads existing Bronze Parquet for this run_date.
2. Applies current extraction rules (potentially updated since the original run).
3. Overwrites Silver standardized_products for this run_date.
4. Re-runs Matching and Insights on the new standardized data.

**Duration**: ~10 minutes.

### Replay: From Matching

Re-runs matching with updated config (thresholds, brand aliases). Use when matching rules were adjusted.

```bash
python -m pipeline.cli replay --run-date 2026-02-25 \
  --start-from matching
```

**What happens**:
1. Reads existing Silver standardized_products for this run_date.
2. Applies current matching config.
3. Overwrites match_candidates and match_map for this run_date.
4. Regenerates review_queue entries (previous pending reviews for this run_date are superseded).
5. Re-runs Insights on the new match data.

**Duration**: ~5 minutes.

**Important**: This will supersede existing review decisions for this run_date. Human-approved matches from the previous matching run are preserved in the audit trail but the new matching run produces fresh candidates.

### Replay: From Insights Only

Re-computes aggregations without changing underlying data. Use when insights config was adjusted.

```bash
python -m pipeline.cli replay --run-date 2026-02-25 \
  --start-from insights
```

**What happens**:
1. Reads existing Silver standardized_products and match_map for this run_date.
2. Reads Silver data for the full window (7/14/30 days before run_date) for delta computations.
3. Applies current insights computation parameters.
4. Overwrites Gold insights_daily for this run_date.

**Duration**: ~2 minutes.

### Replay: Multiple Dates

When a config fix needs to be applied retroactively:

```bash
python -m pipeline.cli replay --run-date-range 2026-02-20:2026-02-25 \
  --start-from standardization
```

This replays each date sequentially from oldest to newest. Sequential ordering is important because insights for later dates depend on data from earlier dates (for delta calculations).

**Duration**: ~10 minutes per date x number of dates.

## Rollback Procedures

### Rollback: Serving Data (Gold Layer)

Restore the Gold serving layer to a previous run's output. Use when the current serving data is known to be bad and a replay is not immediately feasible.

```bash
# List available serving snapshots
python -m pipeline.cli serving snapshots --last 10

# Output:
# Snapshot ID         Run Date     Computed At          Status
# snap_20260225_0430  2026-02-25   2026-02-25T04:30Z    current
# snap_20260224_0415  2026-02-24   2026-02-24T04:15Z    archived
# snap_20260223_0420  2026-02-23   2026-02-23T04:20Z    archived

# Rollback to a previous snapshot
python -m pipeline.cli serving rollback --to-snapshot snap_20260224_0415
```

**What happens**:
1. The current serving snapshot is marked as `rolled_back`.
2. The specified snapshot is promoted to `current`.
3. API queries immediately serve data from the restored snapshot.
4. An audit trail entry is created recording the rollback.

**Duration**: < 1 minute.

**Reversibility**: The rolled-back snapshot is preserved. You can rollback to any available snapshot.

### Rollback: Configuration

Restore pipeline configuration to a previous version:

```bash
# List config history
python -m pipeline.cli config history --last 10

# Output:
# Version  Changed At           Changed By  Changes
# 2.3.1    2026-02-25T10:00Z    user_a      matching.auto_accept_threshold: 0.85 -> 0.80
# 2.3.0    2026-02-20T14:00Z    user_b      extraction_rules.shopee.brand_selector: updated
# 2.2.0    2026-02-15T09:00Z    user_a      brand_aliases: added 5 new brands

# Rollback to a previous config version
python -m pipeline.cli config rollback --to-version 2.3.0
```

**What happens**:
1. The config files are restored to the specified version's state.
2. A new config version is created (e.g., 2.3.2) that records the rollback.
3. The next pipeline run will use the restored config.
4. Does NOT automatically replay any previous runs. You must manually trigger a replay if needed.

### Rollback: Match Map (Nuclear Option)

In extreme cases where match_map is corrupted, restore the entire match_map from a backup:

```bash
# This is a destructive operation. Requires admin role.
python -m pipeline.cli match-map restore --from-backup <backup_id> \
  --confirm "I understand this replaces the current match_map"
```

**What happens**:
1. Current match_map is archived as a backup.
2. Specified backup is restored as the active match_map.
3. Review queue is reset (all pending items are superseded).
4. Insights must be re-computed for all dates in the restored match_map's range.

**Duration**: ~5 minutes plus insights replay time.

**Caution**: This discards all match decisions (auto and human) made since the backup date. Use only as a last resort.

## Replay Checklist

Before executing any replay:

- [ ] Identify the root cause of the data issue.
- [ ] Fix the root cause (rule update, config change, code fix) BEFORE replaying.
- [ ] Determine the correct `start-from` module (do not replay from ingestion unless necessary).
- [ ] Check rate limits if replaying from ingestion.
- [ ] Notify team members that a replay is in progress.
- [ ] After replay, run DQ checks to verify the fix.
- [ ] After replay, spot-check the demo UI.
- [ ] Document the incident and replay in the team log.

## Audit Trail

All replay and rollback operations are recorded in the audit trail:

```json
{
  "audit_id": "aud_abc123",
  "action": "pipeline_replay",
  "user_id": "user_a",
  "timestamp": "2026-02-25T11:00:00Z",
  "details": {
    "run_date": "2026-02-25",
    "start_from": "standardization",
    "reason": "Selector fix for Shopee brand extraction",
    "config_version_before": "2.3.0",
    "config_version_after": "2.3.1",
    "execution_id": "exec_xyz789"
  }
}
```

## Related Documents

- [429-403-handling.md](429-403-handling.md) - Ingestion failure handling
- [field-missing-spike.md](field-missing-spike.md) - Field missing handling
- [alerts-anomaly.md](alerts-anomaly.md) - Output anomaly handling
- [../versioning/version-strategy.md](../versioning/version-strategy.md) - Config versioning
