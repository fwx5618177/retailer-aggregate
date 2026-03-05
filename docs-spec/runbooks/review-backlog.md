# Runbook: Review Queue Backlog

> Severity: P3 (Medium)
> Module: Matching / Review Workflow
> Last updated: 2026-02-25
> On-call team: Data Engineering + Product Operations

## Symptom

The match review queue accumulates more pending items than reviewers can process within the target SLA. Indicators include:

- **Queue depth**: More than 200 pending review items (normal: <50).
- **Review latency**: Average time from enqueue to decision exceeds 48 hours (target: <24 hours).
- **Growth rate**: Queue is growing faster than it is being resolved (daily intake > daily throughput).
- **Aging items**: Items older than 72 hours in `pending` status.

## Impact

- **Matching completeness**: Unreviewed matches are not added to match_map, reducing cross-platform coverage.
- **Insight quality**: Missing matches mean missing cross-platform price comparisons and trend correlations.
- **User experience**: Demo UI shows fewer matched products, making the platform appear less capable.
- **Data debt**: Old review items become harder to review as context becomes stale.

## Root Cause Analysis

| Cause | Likelihood | Diagnostic |
|-------|-----------|------------|
| Increased product catalog (more TopN products) | Medium | Check if top_n was increased or new sub-categories added |
| Matching threshold too low (too many items routed to review) | High | Check review_required band volume vs auto_accepted volume |
| Reviewer capacity reduced (fewer reviewers, holiday, etc.) | Medium | Check reviewer activity logs |
| Matching rule change produced more uncertain scores | Medium | Check if rule_version changed recently |
| New brand/product type with poor extraction (low confidence scores) | Medium | Check if backlog clusters around specific brands/categories |

## Diagnostic Steps

### Step 1: Assess Queue State

```bash
# View current queue metrics
python -m pipeline.cli review-queue stats

# Expected output:
# Total pending: 247
# Total pending > 24h: 183
# Total pending > 72h: 45
# Daily intake (avg 7d): 38
# Daily throughput (avg 7d): 22
# Active reviewers (last 7d): 2
```

### Step 2: Analyze Backlog Composition

```bash
# Break down pending items by sub-category and score band
python -m pipeline.cli review-queue breakdown --status pending

# Expected output:
# Sub-category         Score Band    Count   Avg Age (hours)
# body_wash            0.65-0.75     42      56
# body_wash            0.75-0.85     28      34
# shampoo              0.65-0.75     51      67
# shampoo              0.75-0.85     33      41
# skincare_moisturizer 0.65-0.75     38      48
# ...
```

### Step 3: Check If Threshold Tuning Can Help

```bash
# Analyze the score distribution of pending items
python -m pipeline.cli review-queue score-distribution --status pending

# Check precision of auto-accept if threshold were lowered
python -m pipeline.cli matching evaluate-threshold \
  --new-threshold 0.80 \
  --sample-from review_queue \
  --sample-size 50
```

This simulates what would happen if we lowered the auto-accept threshold from 0.85 to 0.80:
- How many current review items would be auto-accepted?
- What is the estimated precision at the new threshold (based on historical review decisions)?

### Step 4: Check Reviewer Capacity

```bash
# View reviewer activity over the last 14 days
python -m pipeline.cli review-queue reviewer-stats --days 14

# Expected output:
# Reviewer    Decisions/Day  Avg Decision Time  Agreement Rate
# user_a      15             2.3 min            92%
# user_b      7              4.1 min            88%
# (no other active reviewers)
```

## Resolution

### Option 1: Temporarily Raise Auto-Accept Threshold (Quick Win)

If the precision analysis shows that lowering the auto-accept threshold to 0.80 maintains >= 90% precision:

1. **Update the matching config**:
   ```bash
   python -m pipeline.cli config set matching.auto_accept_threshold --value 0.80
   ```

2. **Re-score and auto-accept eligible pending items**:
   ```bash
   python -m pipeline.cli review-queue re-evaluate \
     --new-threshold 0.80 \
     --action auto_accept \
     --dry-run  # First, see what would happen
   ```

3. **If dry-run looks good, execute**:
   ```bash
   python -m pipeline.cli review-queue re-evaluate \
     --new-threshold 0.80 \
     --action auto_accept
   ```

4. **Important**: Set a reminder to revert the threshold after the backlog is cleared:
   ```bash
   python -m pipeline.cli config set matching.auto_accept_threshold --value 0.85 \
     --scheduled-at "2026-03-05T00:00:00Z" \
     --reason "Revert temporary threshold adjustment for backlog"
   ```

### Option 2: Add Reviewers

1. **Grant reviewer role to additional team members**:
   ```bash
   python -m pipeline.cli rbac grant --user <user_id> --role reviewer
   ```

2. **Provide review guidelines** (see Review Guidelines section below).

3. **Assign priority queues** to distribute work:
   ```bash
   # Assign high-priority items (score 0.80-0.85, most likely correct) first
   python -m pipeline.cli review-queue assign \
     --reviewer <new_reviewer_id> \
     --score-min 0.80 \
     --score-max 0.85 \
     --limit 50
   ```

### Option 3: Priority-Based Triage

Focus reviewer effort on the highest-impact items first:

1. **Prioritize by score band** (higher scores are more likely correct and faster to review):
   ```
   Priority 1: Score 0.80-0.85 (likely correct, quick approve)
   Priority 2: Score 0.75-0.80 (moderate confidence, needs brief check)
   Priority 3: Score 0.65-0.75 (low confidence, needs careful review)
   ```

2. **Prioritize by category** (categories with fewer matches benefit more from each review):
   ```bash
   python -m pipeline.cli review-queue prioritize \
     --strategy match_coverage_impact
   ```

3. **Bulk reject obvious no-matches** (items in the 0.65-0.70 band with brand_score < 0.5):
   ```bash
   python -m pipeline.cli review-queue bulk-reject \
     --filter "composite_score < 0.70 AND brand_score < 0.50" \
     --reason "Low brand and composite scores indicate no match" \
     --dry-run
   ```

### Option 4: Fix Root Cause (Brand/Extraction Issues)

If the backlog is driven by poor brand extraction (many products in `unknown_brand` block):

1. **Update brand alias dictionary** with newly discovered brands.
2. **Replay standardization** to improve brand_confidence.
3. **Re-run matching** - better brand extraction leads to higher scores and more auto-accepts.

## Review Guidelines for New Reviewers

When reviewing a match candidate:

1. **Check brand**: Are both products from the same brand? If brands differ, reject.
2. **Check product type**: Are both products the same type (e.g., both shampoo, not shampoo vs conditioner)?
3. **Check size/variant**: If sizes differ, classify as `variant_family`, not `exact_same`.
4. **Use the reasons structure**: The `reasons` JSON explains each signal score. Focus on the lowest-scoring signals.
5. **When in doubt, defer**: Use the `defer` action. Do not force a decision.
6. **Average decision time target**: 2-3 minutes per item. If an item takes >5 minutes, defer it.

## Post-Resolution Monitoring

After applying resolution measures:

1. Track queue depth daily until it returns to <50 pending items.
2. Monitor review quality: check agreement rate between system suggestion and reviewer decision.
3. If threshold was temporarily adjusted, monitor auto-accept precision after reversion.
4. Review the backlog situation weekly to detect trends before they become incidents.

## Escalation

| Condition | Escalation Target | SLA |
|-----------|-------------------|-----|
| Queue depth > 500 | Product Manager | 24 hours |
| Aging items > 7 days | Engineering lead | 48 hours |
| No active reviewers for > 48 hours | Team lead | Immediate |
| Threshold adjustment hurts precision (< 85%) | Engineering lead | Immediate |

## Related Documents

- [../design/matching-design.md](../design/matching-design.md) - Matching algorithm and threshold details
- [replay-rollback.md](replay-rollback.md) - Replay procedures for re-running matching
- [../acceptance/slo-thresholds.md](../acceptance/slo-thresholds.md) - SLO definitions including review latency
