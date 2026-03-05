# Versioning Strategy

> Version: 1.0.0
> Last updated: 2026-02-25
> Status: Accepted

## Overview

The SEA Retailer Intelligence Platform manages three independent version tracks: schema versions, rule versions, and API versions. Each follows semantic versioning (semver) principles but with domain-specific semantics. This document defines the versioning conventions, compatibility rules, and changelog process.

## Version Tracks

| Version Track | Scope | Format | Location |
|---------------|-------|--------|----------|
| `schema_version` | Data table schemas (field names, types, structure) | `MAJOR.MINOR.PATCH` | Recorded in every data row |
| `rule_version` | Processing rules (extraction, matching, insights) | `MAJOR.MINOR.PATCH` | Recorded in every data row |
| `api_version` | REST API contract (endpoints, request/response shapes) | `vN` (integer) | URL path prefix |

## Schema Versioning

### Format

```
schema_version = MAJOR.MINOR.PATCH
Example: 1.3.2
```

### Semantics

| Component | When to Increment | Backward Compatible? |
|-----------|-------------------|---------------------|
| MAJOR | Removing a field, renaming a field, changing a field's type, changing primary key structure | No |
| MINOR | Adding a new nullable field, adding a new table | Yes |
| PATCH | Fixing a field description, adding a constraint that does not reject previously valid data | Yes |

### Compatibility Rules

1. **Readers must tolerate unknown fields**: A reader built for schema 1.2.0 must not fail when encountering data written with schema 1.3.0 (which may have additional fields).
2. **Writers must populate all fields defined in their schema version**: A writer operating at schema 1.3.0 must populate all fields defined up to 1.3.0.
3. **Major version migration window**: When a major version is released, the system supports reading both the old and new major versions for 30 days. After the migration window, old-version data must be migrated or archived.
4. **Mixed-version reads**: Since each row carries its `schema_version`, readers can dynamically handle different versions within the same table (during migration periods).

### Schema Version Lifecycle

```
1.0.0  (Initial release)
  |
  | Add nullable field `variant` to standardized_products
  v
1.1.0  (Minor: new field added)
  |
  | Fix description of `price_thb_satang` field
  v
1.1.1  (Patch: documentation fix)
  |
  | Remove deprecated `raw_units_sold` field from raw_listings
  v
2.0.0  (Major: breaking change)
```

### Schema Change Process

1. **Propose**: Create a schema change proposal describing the change, rationale, and migration plan.
2. **Review**: Team reviews the proposal. Verify backward compatibility classification.
3. **Implement**: Update the schema definition and the code that reads/writes the affected tables.
4. **Migrate** (if major): Write a migration script that transforms existing data to the new schema.
5. **Deploy**: Roll out the change. Record the new schema_version in all subsequent writes.
6. **Verify**: Run DQ checks to confirm no data corruption during migration.

## Rule Versioning

### Format

```
rule_version = MAJOR.MINOR.PATCH
Example: 2.5.0
```

Rules encompass all configurable processing logic:
- Extraction rules (CSS selectors, JSON paths, regex patterns)
- Brand alias dictionaries
- Matching weights and thresholds
- Insights computation parameters

### Semantics

| Component | When to Increment | Impact |
|-----------|-------------------|--------|
| MAJOR | Changing matching weight distribution, changing threshold bands, adding/removing a signal | Results change significantly. Historical comparison may be invalid. |
| MINOR | Adding new brand aliases, updating extraction selectors, adjusting a single threshold by <= 10% | Results change incrementally. Historical comparison is still meaningful. |
| PATCH | Fixing a typo in a brand alias, correcting a regex bug that caused extraction failures | Fixes incorrect behavior. Results should improve, not change methodology. |

### Compatibility Rules

1. **Rule versions are NOT backward compatible by design**: Changing rules changes output. The purpose of rule versioning is traceability, not compatibility.
2. **Every output row records its rule_version**: This enables comparing outputs produced by different rule versions.
3. **Retroactive reprocessing**: When rule changes are significant (major version), consider replaying historical data with the new rules to maintain consistency. See [replay-rollback runbook](../runbooks/replay-rollback.md).
4. **A/B testing**: Before deploying a major rule change, run both the old and new rules on the same input data and compare outputs.

### Rule Configuration Structure

```yaml
# config/matching_config.yaml
rule_version: "2.5.0"
last_updated: "2026-02-25"
updated_by: "user_a"

matching:
  weights:
    brand: 0.30
    spec: 0.25
    title: 0.30
    price: 0.15
  thresholds:
    auto_accept: 0.85
    review_required: 0.65
  blocking:
    tfidf_prefilter_min: 0.20
```

### Rule Change Process

1. **Propose**: Describe the rule change, expected impact, and testing plan.
2. **Test**: Run the new rules on a sample of recent data and compare with current output.
3. **Review**: Present comparison results. Get approval from the data quality owner.
4. **Deploy**: Update the config file and bump `rule_version`.
5. **Monitor**: Watch DQ metrics and match quality for 3 days after deployment.
6. **Decide on retroactive replay**: If the change is significant, decide whether to replay historical dates.

## API Versioning

### Format

```
api_version = vN (integer, in URL path)
Example: /api/v1/insights/rankings
```

### Semantics

The API version is a single integer that increments only on breaking changes:

| Change Type | Version Impact | Example |
|-------------|---------------|---------|
| Adding a new endpoint | No version change | Add GET `/api/v1/insights/brands` |
| Adding a new optional query parameter | No version change | Add `?brand_filter=NIVEA` |
| Adding a new field to response body | No version change | Add `brand_share_pct` to response |
| Removing an endpoint | New version (v2) | Remove GET `/api/v1/insights/movers` |
| Removing a field from response body | New version (v2) | Remove `units_sold` from response |
| Changing a field's type in response | New version (v2) | Change `price` from integer to string |
| Changing authentication mechanism | New version (v2) | Switch from API key to OAuth |

### Compatibility Rules

1. **Additive changes are always safe**: New endpoints, optional parameters, and additional response fields do not require a version bump.
2. **Deprecation before removal**: Before removing a field or endpoint in v(N+1), mark it as deprecated in v(N) for at least 30 days.
3. **Parallel operation**: When v2 is released, v1 continues to operate for at least 90 days.
4. **Version sunset notice**: Communicate version sunset at least 60 days in advance.
5. **Version header**: All responses include `X-API-Version: v1` header for client verification.

### API Version Lifecycle

```
v1 (current)  -  Active
  |
  | Breaking change needed
  v
v1 (deprecated) + v2 (active)  -  Parallel for 90 days
  |
  | After 90 days
  v
v1 (sunset) + v2 (active)  -  v1 returns 410 Gone
```

### Deprecation Response Headers

When an endpoint or field is deprecated:
```
Sunset: Sat, 30 May 2026 00:00:00 GMT
Deprecation: true
Link: <https://api.sea-retailer.example.com/api/v2/insights/rankings>; rel="successor-version"
```

## Changelog Process

### Format

Every version change (schema, rule, or API) is recorded in a structured changelog.

```markdown
## [rule_version 2.5.0] - 2026-02-25

### Changed
- Updated matching weight for brand signal from 0.25 to 0.30.
- Updated matching weight for price signal from 0.20 to 0.15.

### Added
- 15 new brand aliases for Thai domestic brands.

### Impact
- Expected: ~5% increase in auto-accept rate due to higher brand weight.
- Retroactive replay: Not required (minor adjustment).
- Monitoring period: 3 days.
```

### Changelog Storage

| Version Track | Changelog Location |
|---------------|-------------------|
| `schema_version` | `CHANGELOG-schema.md` in the repository root |
| `rule_version` | `CHANGELOG-rules.md` in the repository root |
| `api_version` | `CHANGELOG-api.md` in the repository root |

### Changelog Requirements

1. Every version bump MUST have a changelog entry before merging.
2. Changelog entries follow the [Keep a Changelog](https://keepachangelog.com/) format.
3. Categories: Added, Changed, Deprecated, Removed, Fixed, Security.
4. Each entry includes an Impact section describing expected behavioral changes.
5. Changelogs are append-only. Historical entries are never modified.

## Version Tracking in Code

### Data Rows

Every row in every table includes:
```json
{
  "schema_version": "1.3.0",
  "rule_version": "2.5.0"
}
```

### API Responses

Every API response includes:
```json
{
  "meta": {
    "api_version": "v1",
    "data_schema_version": "1.3.0",
    "data_rule_version": "2.5.0"
  }
}
```

### Pipeline Run Manifest

```json
{
  "run_id": "shopee_personal_care_2026-02-25",
  "schema_version": "1.3.0",
  "rule_version": "2.5.0",
  "config_hash": "sha256:abc123..."
}
```

## Related Documents

- [../design/data-model.md](../design/data-model.md) - Schema definitions for all tables
- [../design/api-design.md](../design/api-design.md) - API endpoint specifications
- [../design/matching-design.md](../design/matching-design.md) - Matching rules and thresholds
- [../runbooks/replay-rollback.md](../runbooks/replay-rollback.md) - Replay procedures for rule version changes
