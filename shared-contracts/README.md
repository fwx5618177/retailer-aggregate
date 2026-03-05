# shared-contracts

Single source of truth for all cross-repo schemas, enums, OpenAPI specs, and generated types for the SEA Retailer Top Selling Intelligence platform.

## Structure

```
shared-contracts/
  openapi/api-v1.yaml        # OpenAPI 3.1 specification (7 endpoints)
  schemas/                    # JSON Schema definitions
    enums.json               # All shared enumerations
    top_items.json           # Top items table schema
    price_snapshots.json     # Price snapshots schema
    sales_proxy.json         # Sales proxy schema
    match_map_platform.json  # Cross-platform matching results
    our_mapping.json         # Our internal mapping status
    alerts.json              # Alerts/opportunities schema
    reasons.json             # Structured matching reasons
    manifest.json            # Pipeline/matching run manifest
  generated/
    python/                  # Python Pydantic models & enums
    typescript/              # TypeScript interfaces & enums
```

## Usage

### Python
```python
from sea_retailer_contracts import TopItem, MatchType, Platform
```

### TypeScript
```typescript
import { TopItem, MatchType, Platform } from './generated/typescript/src';
```

## Versioning
- `schema_version`: Follows semver (e.g., "1.0.0")
- Breaking changes require major version bump
- All generated types are committed to the repo
