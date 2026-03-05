# Runbook: Field Missing Rate Spike

> Severity: P2 (High)
> Module: Standardization
> Last updated: 2026-02-25
> On-call team: Data Engineering

## Symptom

The standardization module's data quality report shows a spike in field missing rates beyond the acceptable thresholds:

- `brand` missing rate exceeds 20% (SLO: <= 20%)
- `price` missing rate exceeds 2% (SLO: <= 2%)
- `review_count` missing rate exceeds 5% (SLO: <= 5%)
- Any field that was previously at 0% missing now shows >1% missing

This is detected by the post-standardization DQ checks and surfaced in the pipeline run summary.

## Impact

- **Matching quality**: Missing brand fields prevent proper blocking, reducing match recall.
- **Insight accuracy**: Missing prices or review counts produce null deltas in the insights layer.
- **Data trust**: Downstream consumers see incomplete records, degrading confidence in the platform.
- **SLO breach**: Sustained field missing spikes may breach the <=5% overall field missing SLO.

## Root Cause Analysis

| Cause | Likelihood | Diagnostic |
|-------|-----------|------------|
| Platform changed page structure (HTML/CSS selectors broken) | High | Compare raw HTML structure of failing products with expected selectors |
| Platform A/B testing different page layouts | Medium | Check if failures cluster on specific product IDs or are random |
| New product type with different page structure | Medium | Check if failures correlate with specific sub-categories |
| Anti-bot measures returning partial pages | Medium | Check raw_payload size of failing products vs successful ones |
| Network issues causing truncated responses | Low | Check fetch_http_status and response content-length |

## Diagnostic Steps

### Step 1: Quantify the Spike

```bash
# View field completeness report for the current run
python -m pipeline.cli dq-report --run-id <current_run_id> --type field_completeness

# Compare with previous runs
python -m pipeline.cli dq-report --run-id <previous_run_id> --type field_completeness
```

Expected output:
```
Field               Current  Previous  Delta   Status
brand               82%      95%       -13%    ALERT
price               97%      99.5%     -2.5%   ALERT
review_count        93%      98%       -5%     WARN
title               100%     100%      0%      OK
rank                100%     100%      0%      OK
```

### Step 2: Identify Affected Scope

```bash
# Break down missing fields by platform and sub-category
python -m pipeline.cli dq-report --run-id <current_run_id> \
  --type field_completeness \
  --group-by platform,sub_category
```

Determine if the issue is:
- **Platform-specific**: Only Shopee or only TikTok Shop (suggests selector breakage).
- **Category-specific**: Only one sub-category (suggests category page layout change).
- **Random**: Across all platforms/categories (suggests network issue or anti-bot).

### Step 3: Inspect Raw Data

```bash
# Sample 5 failing products and inspect raw payloads
python -m pipeline.cli inspect-raw --run-id <current_run_id> \
  --field-missing brand \
  --sample 5 \
  --output /tmp/raw_samples/
```

Manually examine the raw HTML/JSON to determine:
1. Is the data present in the raw payload but not extracted? (Selector issue)
2. Is the data absent from the raw payload entirely? (Platform change)
3. Is the raw payload truncated or malformed? (Fetch issue)

### Step 4: Test Current Selectors

```bash
# Run extraction rules against raw samples without writing to Silver
python -m pipeline.cli test-extraction --input /tmp/raw_samples/ \
  --platform <platform> --verbose
```

This outputs which selectors matched and which failed, with the specific extraction error.

## Resolution

### Scenario A: Selector Breakage (Most Common)

1. **Update extraction rules**:
   ```bash
   # Edit the platform-specific extraction config
   vim config/extraction_rules/<platform>.yaml
   ```

2. **Test the fix against raw samples**:
   ```bash
   python -m pipeline.cli test-extraction --input /tmp/raw_samples/ \
     --platform <platform> --config config/extraction_rules/<platform>.yaml
   ```

3. **Replay raw data through standardization** (does not re-fetch):
   ```bash
   python -m pipeline.cli replay --run-id <current_run_id> \
     --start-from standardization \
     --platform <platform>
   ```

4. **Bump rule_version** in the config (see [versioning strategy](../versioning/version-strategy.md)).

5. **Verify the fix**:
   ```bash
   python -m pipeline.cli dq-report --run-id <current_run_id> --type field_completeness
   ```

### Scenario B: Platform Changed Data Availability

If the field is genuinely no longer available from the platform (e.g., TikTok removed units_sold):

1. **Document the change** in the platform-specific notes.
2. **Adjust DQ thresholds** for the affected field to reflect the new reality.
3. **Update downstream modules** to handle the field as optional.
4. **Communicate** to stakeholders that the field is no longer available.

### Scenario C: Partial/Truncated Responses

1. **Re-fetch the affected products**:
   ```bash
   python -m pipeline.cli retry --run-id <current_run_id> \
     --status success \
     --field-missing brand \
     --force-refetch
   ```

2. **Re-run standardization**:
   ```bash
   python -m pipeline.cli replay --run-id <current_run_id> \
     --start-from standardization
   ```

## Post-Resolution Verification

After applying the fix:

1. Confirm field completeness is back within SLO thresholds.
2. Verify downstream match quality is not impacted:
   ```bash
   python -m pipeline.cli dq-report --run-id <current_run_id> --type match_quality
   ```
3. Spot-check 10 random products in the demo UI to verify data displays correctly.
4. Monitor the next 3 daily runs to confirm the fix holds.

## Prevention

- **Selector health checks**: Run a daily canary that tests all extraction selectors against a small sample of fresh pages, independent of the full pipeline.
- **Multi-selector fallback**: Configure 2-3 fallback selectors per field so that a single selector breakage is covered.
- **Raw payload archival**: Always store the complete raw payload so that re-extraction is possible without re-fetching.
- **Version control for rules**: All extraction rules are versioned. Changes go through code review.

## Escalation

| Condition | Escalation Target | SLA |
|-----------|-------------------|-----|
| Field missing > 20% for price or title | Engineering lead | Immediate |
| Selector fix requires code change (not config) | Engineering lead | 4 hours |
| Platform removed a critical field permanently | Product Manager | Next business day |
| Spike affects multiple platforms simultaneously | Full team | Immediate |

## Related Documents

- [replay-rollback.md](replay-rollback.md) - Full replay procedure
- [../acceptance/dq-thresholds.md](../acceptance/dq-thresholds.md) - DQ threshold definitions
- [../design/system-design.md](../design/system-design.md) - Standardization module design
