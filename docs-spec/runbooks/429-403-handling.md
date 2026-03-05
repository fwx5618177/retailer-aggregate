# Runbook: HTTP 429/403 Scraping Failure Handling

> Severity: P2 (High)
> Module: Ingestion
> Last updated: 2026-02-25
> On-call team: Data Engineering

## Symptom

The ingestion pipeline encounters elevated rates of HTTP 429 (Too Many Requests) or HTTP 403 (Forbidden) responses from Shopee Thailand or TikTok Shop Thailand. This manifests as:

- Pipeline run manifest shows `fetch_failed` count exceeding 10% of expected products.
- Monitoring dashboard shows 429/403 spike for the affected platform.
- Pipeline completion time exceeds the expected window (normally < 90 minutes).

## Impact

- **Data freshness**: Affected platform's data for the run_date is incomplete or missing.
- **Insights quality**: TopN coverage drops below the 95% SLO threshold.
- **Matching**: Reduced products on one platform means fewer cross-platform matches.
- **User-facing**: Demo UI may show stale data or missing products for the affected platform.

## Root Cause Analysis

### HTTP 429 (Rate Limited)

| Cause | Likelihood | Diagnostic |
|-------|-----------|------------|
| Our request rate exceeded platform's limit | High | Check request rate in logs vs configured rate limit |
| Platform lowered their rate limit | Medium | Compare with historical successful rate |
| Shared IP pool is over-utilized | Medium | Check proxy provider dashboard for concurrent usage |

### HTTP 403 (Forbidden/Blocked)

| Cause | Likelihood | Diagnostic |
|-------|-----------|------------|
| IP/proxy blocked by platform | High | Test manual request from same proxy; try different proxy |
| Platform added new bot detection | Medium | Check if User-Agent or TLS fingerprint changed requirements |
| Platform geo-restricted access | Low | Verify proxy is Thailand-based for TH marketplace |
| Session/cookie invalidation | Medium | Check if platform requires fresh session cookies |

## Immediate Response (First 15 Minutes)

### Step 1: Assess Scope

1. Check the pipeline run manifest for the current run:
   ```bash
   python -m pipeline.cli status --run-id <current_run_id>
   ```
2. Identify which platform and sub-categories are affected.
3. Count the number of 429 vs 403 errors:
   ```bash
   python -m pipeline.cli errors --run-id <current_run_id> --group-by http_status
   ```

### Step 2: Reduce Request Rate (for 429)

1. Reduce the rate limit to 50% of current setting:
   ```bash
   python -m pipeline.cli config set ingestion.rate_limit.<platform> --value <current/2>
   ```
   - Shopee default: 2 req/s -> reduce to 1 req/s
   - TikTok Shop default: 1 req/s -> reduce to 0.5 req/s

2. Wait 5 minutes for rate limit window to reset.

3. Resume the pipeline for failed products only:
   ```bash
   python -m pipeline.cli retry --run-id <current_run_id> --status fetch_failed
   ```

### Step 3: Rotate Proxy (for 403)

1. Force proxy rotation to a fresh IP:
   ```bash
   python -m pipeline.cli proxy rotate --platform <platform>
   ```

2. Test connectivity with a single product fetch:
   ```bash
   python -m pipeline.cli test-fetch --platform <platform> --product-id <any_known_id>
   ```

3. If test succeeds, retry failed products:
   ```bash
   python -m pipeline.cli retry --run-id <current_run_id> --status fetch_failed
   ```

4. If test fails, escalate to proxy provider (see Escalation section).

### Step 4: Fallback to Stub Data (if retry exhausted)

If after 3 retry cycles the failure rate remains above 10%:

1. Mark the platform as `degraded` for this run_date:
   ```bash
   python -m pipeline.cli mark-degraded --run-id <current_run_id> --platform <platform>
   ```

2. Generate stub entries for missing products using last known data:
   ```bash
   python -m pipeline.cli fallback-stub --run-id <current_run_id> --source previous_run
   ```
   Stub entries carry `fetch_status: stub_from_previous` and `dq_flags: {"is_stub": true}`.

3. The standardization and downstream modules will process stubs normally but the DQ dashboard will flag stub percentage.

### Step 5: Mark Data as Degraded

1. Add a degradation marker to the run manifest:
   ```bash
   python -m pipeline.cli annotate --run-id <current_run_id> \
     --key degraded_platforms --value <platform> \
     --key degradation_reason --value "429/403 failure, stub fallback applied"
   ```

2. The API layer reads this marker and includes it in response metadata:
   ```json
   {
     "meta": {
       "data_quality": "degraded",
       "degraded_platforms": ["tiktok_shop"],
       "degradation_reason": "Elevated 403 errors during ingestion. 15% of products are stubs from previous run."
     }
   }
   ```

## Recovery Actions (Next 24 Hours)

1. **Monitor next scheduled run**: Verify that the next daily run completes without elevated errors.
2. **Rate limit tuning**: If 429 was the issue, keep the reduced rate for 48 hours before gradually increasing.
3. **Proxy pool health**: Request proxy provider report on IP reputation for affected IPs.
4. **Platform change detection**: Check if the platform's page structure or API changed (may require selector updates).

## Escalation

| Condition | Escalation Target | SLA |
|-----------|-------------------|-----|
| 403 persists after proxy rotation | Proxy provider support | 4 hours |
| Platform structure changed | Data Engineering lead | Next business day |
| Degraded state for >2 consecutive days | Product Manager + Engineering lead | Immediate |
| All proxies blocked simultaneously | Engineering lead + Proxy provider | 2 hours |

## Prevention

- Maintain a pool of at least 10 rotating residential proxies per platform.
- Implement progressive rate limiting that automatically reduces on first 429.
- Run a daily "canary" test fetch before the full pipeline to detect blocks early.
- Monitor proxy provider's IP reputation scores weekly.
- Keep request patterns randomized (variable delays, randomized user-agents, session rotation).

## Related Documents

- [replay-rollback.md](replay-rollback.md) - How to replay the pipeline after fixing the issue
- [alerts-anomaly.md](alerts-anomaly.md) - Alert handling for downstream anomalies caused by degraded ingestion
- [../compliance/data-sources.md](../compliance/data-sources.md) - Rate limiting and ToS compliance
