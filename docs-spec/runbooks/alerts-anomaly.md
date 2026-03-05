# Runbook: Alert Output Anomaly

> Severity: P2 (High)
> Module: Insights / Gold Layer
> Last updated: 2026-02-25
> On-call team: Data Engineering

## Symptom

The insights module produces output that deviates significantly from expected patterns. This includes:

- **Rank distribution anomaly**: Sudden shift in rank distribution (e.g., all ranks clustered near 1 or near 200).
- **Price anomaly**: Average price shifts by more than 20% day-over-day without a known cause (e.g., platform-wide sale).
- **Volume anomaly**: Total product count in insights_daily deviates by more than 10% from expected.
- **Match rate anomaly**: Cross-platform match rate drops or spikes by more than 15 percentage points.
- **Delta anomaly**: Computed deltas (rank_delta, review_count_delta, price_change_pct) show implausible values.

These anomalies are detected by post-computation quality checks that compare the current run's output distribution against a rolling 7-day baseline.

## Impact

- **Misleading insights**: Users see incorrect trend data, undermining trust in the platform.
- **Incorrect cross-platform comparison**: Bad price or rank data produces meaningless comparisons.
- **Downstream decisions**: If stakeholders act on anomalous data, it could lead to wrong business conclusions.

## Diagnostic Steps

### Step 1: Verify the Anomaly Is Real

Before acting, confirm that the anomaly is in the output (not a false alarm from the detection system):

```bash
# View the anomaly detection report
python -m pipeline.cli anomaly-report --run-id <current_run_id>

# Compare key distributions
python -m pipeline.cli distribution-compare \
  --run-id <current_run_id> \
  --baseline-run-ids <last_7_run_ids> \
  --fields rank,price_thb_satang,review_count
```

### Step 2: Check Input Quality

Anomalous output usually originates from anomalous input. Check upstream layers:

```bash
# Check Bronze layer (raw data) quality
python -m pipeline.cli dq-report --run-id <current_run_id> --layer bronze

# Check Silver layer (standardized data) quality
python -m pipeline.cli dq-report --run-id <current_run_id> --layer silver

# Check match_map quality
python -m pipeline.cli dq-report --run-id <current_run_id> --layer match
```

Common input issues that cause output anomalies:

| Input Issue | Output Anomaly |
|-------------|---------------|
| Ingestion pulled wrong category | Rank distribution shift, unfamiliar brands |
| Price extraction broken (returns 0 or null) | Price average collapse |
| Duplicate products in raw data | Inflated product count |
| Matching config changed unexpectedly | Match rate spike/drop |
| Previous run's data corrupted (delta calculation base) | Implausible deltas |

### Step 3: Identify the Root Cause

Based on the input quality check, determine which scenario applies:

#### Scenario A: Bad Input Data

The Bronze or Silver layer has quality issues. Follow the appropriate runbook:
- Field missing spike -> [field-missing-spike.md](field-missing-spike.md)
- Ingestion failures -> [429-403-handling.md](429-403-handling.md)

#### Scenario B: Config Drift

A configuration change caused the anomaly:

```bash
# Check if any config changed since the last successful run
python -m pipeline.cli config diff --from-run <last_good_run_id> --to-run <current_run_id>
```

This shows any changes in:
- Extraction rules (rule_version)
- Matching thresholds (matching_config)
- Insights computation parameters
- Platform-specific settings

#### Scenario C: Legitimate Market Event

The data is correct; the market actually shifted (e.g., a major sale event, product recall, platform algorithm change):

```bash
# Check if the platform has a known sale event
# This is a manual check - review platform's event calendar
# Also check if the anomaly affects all sub-categories or just one
python -m pipeline.cli anomaly-report --run-id <current_run_id> --group-by sub_category
```

If the anomaly is real market data, no fix is needed, but document the event.

### Step 4: Check for Code/Logic Bugs

If input data and config look correct, the issue may be in the insights computation logic:

```bash
# Run insights computation in debug mode on a small sample
python -m pipeline.cli compute-insights --run-id <current_run_id> \
  --debug --sample 20 --verbose
```

Review the debug output for:
- Off-by-one errors in window calculations
- Division by zero in delta computations
- Incorrect join logic between match_map and standardized_products
- Timezone issues in date comparisons

## Resolution

### Fix A: Rollback Config and Rerun

If the cause is config drift:

1. **Identify the last known good config version**:
   ```bash
   python -m pipeline.cli config history --last 5
   ```

2. **Rollback to the good config**:
   ```bash
   python -m pipeline.cli config rollback --to-version <good_version>
   ```

3. **Rerun the insights computation** (not the full pipeline):
   ```bash
   python -m pipeline.cli replay --run-id <current_run_id> \
     --start-from insights
   ```

4. **Verify output**:
   ```bash
   python -m pipeline.cli anomaly-report --run-id <current_run_id>
   ```

### Fix B: Rerun from Upstream Fix

If the cause is bad input data and the upstream issue has been fixed:

```bash
python -m pipeline.cli replay --run-id <current_run_id> \
  --start-from <fixed_module>
```

Where `<fixed_module>` is the earliest module that was affected (e.g., `standardization` if selectors were fixed).

### Fix C: Document and Accept (Market Event)

If the anomaly is legitimate:

1. **Add an annotation to the run**:
   ```bash
   python -m pipeline.cli annotate --run-id <current_run_id> \
     --key market_event --value "Shopee 2.25 mega sale" \
     --key anomaly_accepted --value "true"
   ```

2. **Suppress the anomaly alert for this run** so it does not trigger again:
   ```bash
   python -m pipeline.cli alert suppress --run-id <current_run_id> --reason "Known market event"
   ```

### Fix D: Hotfix for Code Bug

If a code bug is identified:

1. Fix the bug in the insights computation logic.
2. Write a test case that reproduces the anomaly.
3. Deploy the fix.
4. Rerun insights for the affected run_date(s).

## Post-Resolution Verification

1. Confirm the anomaly report shows no flags after rerun.
2. Spot-check 10 products in the demo UI for data correctness.
3. Verify that the next daily run produces normal output.
4. If config was rolled back, schedule a proper config review before re-applying the change.

## Escalation

| Condition | Escalation Target | SLA |
|-----------|-------------------|-----|
| Anomaly persists after config rollback and rerun | Engineering lead | 2 hours |
| Code bug identified | Engineering lead | 4 hours |
| Anomaly affects all platforms and categories | Full team | Immediate |
| Data served to external consumers with anomaly | Product Manager + Engineering lead | Immediate |

## Prevention

- **Config change reviews**: All config changes require a review and are deployed with a canary run.
- **Automated anomaly detection**: Post-computation checks compare against a 7-day rolling baseline.
- **Immutable audit trail**: All config versions are logged so drift is always traceable.
- **Market event calendar**: Maintain a calendar of known sale events (e.g., Shopee 2.2, 3.3, Lazada birthday sale) to pre-suppress expected anomalies.

## Related Documents

- [replay-rollback.md](replay-rollback.md) - Full replay and rollback procedures
- [field-missing-spike.md](field-missing-spike.md) - Upstream field missing handling
- [../acceptance/slo-thresholds.md](../acceptance/slo-thresholds.md) - SLO definitions
