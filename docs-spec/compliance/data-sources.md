# Data Source Compliance

> Version: 1.0.0
> Last updated: 2026-02-25
> Status: Accepted
> Review cadence: Quarterly

## Overview

This document defines the data source priority hierarchy, Terms of Service (ToS) compliance requirements, rate limiting policies, and fallback strategies for the SEA Retailer Intelligence Platform. All data collection activities must adhere to these guidelines.

## Data Source Priority Hierarchy

Data sources are ranked in order of preference. Always use the highest-priority source available:

### Priority 1: Official API (Preferred)

| Attribute | Detail |
|-----------|--------|
| Source | Platform-provided official APIs (e.g., Shopee Open Platform API) |
| Compliance risk | Lowest - explicitly sanctioned by the platform |
| Data quality | Highest - structured, versioned, documented |
| Rate limits | Clearly defined in API documentation |
| Requirements | API key registration, affiliate/partner program enrollment |

**Current status**:
- **Shopee**: Open Platform API available for product search and detail. Requires Shopee Partner Program enrollment. Application submitted, pending approval.
- **TikTok Shop**: No public API available for product catalog browsing as of 2026-02. TikTok Shop Seller API exists but is restricted to sellers managing their own shops.

**When to use**: Always, when available and when the API provides the required data fields.

### Priority 2: Compliant Third-Party Data Providers

| Attribute | Detail |
|-----------|--------|
| Source | Licensed data aggregators who have formal data-sharing agreements with platforms |
| Compliance risk | Low - the provider is responsible for platform compliance |
| Data quality | High - typically cleaned and structured |
| Rate limits | Defined by provider SLA |
| Requirements | Commercial contract, data usage agreement |

**Evaluation criteria for third-party providers**:
1. Provider has a documented data license or partnership with the source platform.
2. Provider's terms of use permit our use case (competitive intelligence, analytics).
3. Provider does not require us to redistribute the raw data.
4. Provider can supply the specific fields we need (rank, price, review_count, brand).
5. Provider covers Thailand market for personal_care category.

**Current status**: No third-party provider contracted for MVP. To be evaluated post-MVP if official API access is not obtained.

### Priority 3: Self-Crawl (Fallback)

| Attribute | Detail |
|-----------|--------|
| Source | Direct structured scraping of publicly accessible web pages |
| Compliance risk | Medium to High - must strictly comply with ToS and robots.txt |
| Data quality | Medium - subject to page structure changes and anti-bot measures |
| Rate limits | Self-imposed, conservative |
| Requirements | Strict adherence to all constraints below |

**When to use**: Only when Priority 1 and Priority 2 are not available or do not cover the required data.

## Terms of Service (ToS) Constraints

### General Principles

1. **Respect ToS**: Read and comply with each platform's Terms of Service. Do not access data that ToS explicitly prohibits from automated collection.
2. **Public data only**: Only collect data that is publicly visible to any user browsing the platform without authentication.
3. **No authentication bypass**: Do not circumvent login walls, CAPTCHAs, or access controls.
4. **No personal data**: Do not collect seller personal information, buyer reviews with personally identifiable information (PII), or any data subject to PDPA (Thailand's Personal Data Protection Act).
5. **Purpose limitation**: Data is collected solely for competitive intelligence analytics. It is not redistributed, resold, or used to undercut individual sellers.

### Platform-Specific ToS Notes

#### Shopee Thailand (`shopee.co.th`)

| Constraint | Our Compliance |
|------------|---------------|
| ToS prohibits automated scraping | We prefer the Open Platform API (Priority 1). Self-crawl is a fallback only. |
| Best-seller listings are publicly accessible | We only collect publicly visible listing data. |
| Rate limits on web pages | We enforce conservative self-imposed rate limits (see below). |
| Product data display for analytics | We aggregate and anonymize data; we do not republish individual listings. |

#### TikTok Shop Thailand

| Constraint | Our Compliance |
|------------|---------------|
| No public API for catalog browsing | Self-crawl is currently the only option. |
| ToS prohibits automated access | We implement conservative rate limiting and respectful crawling practices. |
| Public product pages are accessible | We only access publicly browsable category and product pages. |

### Legal Review

- The compliance team reviews ToS for each platform quarterly.
- Any ToS change that affects our data collection triggers an immediate review.
- If a platform explicitly contacts us to stop crawling, we comply immediately and escalate to management.

## Robots.txt Compliance

### Policy

We respect `robots.txt` directives for all self-crawl activities:

1. **Check robots.txt** before crawling any new path on a platform.
2. **Cache robots.txt** for 24 hours. Re-fetch daily.
3. **Obey Disallow directives**: Do not crawl paths that are disallowed for our user-agent or for `*`.
4. **Respect Crawl-delay**: If specified, use the platform's crawl-delay as a minimum interval between requests.
5. **User-agent identification**: Use a descriptive User-Agent string: `SEARetailerBot/1.0 (+https://sea-retailer.example.com/bot-info)`.

### Implementation

```python
# Pseudo-code for robots.txt checking
def is_allowed(url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    robots = fetch_cached_robots(robots_url, cache_ttl=86400)
    return robots.can_fetch("SEARetailerBot/1.0", url)
```

### Current robots.txt Analysis

| Platform | Key Disallowed Paths | Allowed Paths We Use |
|----------|---------------------|---------------------|
| shopee.co.th | `/api/*`, `/user/*`, `/buyer/*` | `/search/*`, product detail pages |
| tiktokshop.com | `/api/*`, `/seller/*` | Category browsing pages, product detail pages |

## Rate Limiting Policy

### Self-Imposed Rate Limits

We enforce rate limits stricter than what platforms typically allow, as a good-faith measure:

| Platform | Rate Limit | Burst | Rationale |
|----------|-----------|-------|-----------|
| Shopee Thailand | 2 requests/second | Max 5 concurrent | Conservative for a large marketplace |
| TikTok Shop Thailand | 1 request/second | Max 2 concurrent | More conservative due to no official API |

### Adaptive Rate Limiting

The system automatically adjusts rates based on platform responses:

| Signal | Action |
|--------|--------|
| HTTP 429 received | Reduce rate to 50% of current. Wait for `Retry-After` header or 60s. |
| 3 consecutive 429s | Pause for 5 minutes, then resume at 25% of original rate. |
| HTTP 403 received | Rotate proxy. If 403 persists after 3 rotations, pause platform for 30 minutes. |
| Sustained 200s for 10 minutes | Gradually increase rate by 10% until reaching the configured maximum. |

### Request Scheduling

- Requests are distributed evenly over time (not burst-then-wait).
- Random jitter of 0.1-0.5s is added between requests to avoid predictable patterns.
- Daily runs are scheduled during off-peak hours (02:00-05:00 UTC+7) to minimize load on platforms.

## Fallback Strategy

When a data source becomes unavailable, the system follows this fallback chain:

### Level 1: Retry with Backoff

```
Attempt 1: Normal request
Attempt 2: Wait 1s, retry
Attempt 3: Wait 4s, retry with rotated proxy
Attempt 4: Wait 16s, retry with rotated proxy
```

### Level 2: Degraded Mode

If retries exhaust:
1. Mark the product/platform as `degraded` in the run manifest.
2. Continue pipeline for remaining products (do not fail the entire run).
3. Log the failure with full context for debugging.

### Level 3: Stub from Previous Run

For products that failed in Level 2:
1. Copy the previous run's data for the same product.
2. Mark with `fetch_status: stub_from_previous` and `dq_flags: {"is_stub": true}`.
3. Stub data retains the previous run's values but increments the `run_date`.
4. Stubs are valid for a maximum of 3 consecutive days. After that, the product is dropped from the TopN.

### Level 4: Source Switch

If an entire platform is unavailable for >24 hours:
1. Evaluate alternative data sources (e.g., switch from self-crawl to a third-party provider).
2. Escalate to engineering lead and product manager.
3. Communicate data gaps to stakeholders.

## Data Retention and Deletion

| Data Type | Retention | Deletion Method |
|-----------|-----------|----------------|
| Raw responses (Bronze) | 90 days | Partition drop |
| Standardized data (Silver) | 180 days | Partition drop |
| Serving data (Gold) | Indefinite | Monthly compaction |
| Audit logs | Indefinite | Never deleted |

If a platform requests deletion of specific data, we comply within 72 hours and document the request in the compliance log.

## Compliance Checklist (Quarterly Review)

- [ ] Review ToS for Shopee Thailand for changes.
- [ ] Review ToS for TikTok Shop Thailand for changes.
- [ ] Verify robots.txt compliance for all crawled paths.
- [ ] Review rate limit effectiveness (429/403 rate should be <1%).
- [ ] Verify no PII is collected or stored.
- [ ] Review third-party provider options for Priority 2 upgrade.
- [ ] Update this document with any changes.

## Related Documents

- [../runbooks/429-403-handling.md](../runbooks/429-403-handling.md) - Handling rate limit and block errors
- [../design/system-design.md](../design/system-design.md) - Ingestion module design
- [../scope/mvp-scope.md](../scope/mvp-scope.md) - Target platforms and data scope
