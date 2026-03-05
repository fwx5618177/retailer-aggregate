# SEA Retailer Data Pipeline

Python data pipeline for ingesting, standardizing, quality-checking, and exporting top-selling item data from TikTok Shop and Shopee.

## Quick Start

```bash
# Install dependencies (requires Python >=3.12)
pip install -e ".[dev]"

# Run with stub data (offline)
python -m sea_pipeline run --config config/default.yaml --config-override config/stub.yaml

# Run tests
pytest tests/ -v
```

## Architecture

```
Ingest → Standardise → DQ Check → Export (DuckDB + Parquet)
```

### Pipeline Steps

1. **Ingestion**: Fetch top items from platform APIs (or load stub data)
2. **Standardisation**: Normalize brands, parse specs (size/unit), handle currency
3. **DQ Checks**: Validate TopN coverage, field completeness, rank uniqueness, currency consistency
4. **DQ Gate**: Pass/warn/block based on check results
5. **Export**: Write to DuckDB tables + Parquet files in `data/serving/`
6. **Alerts**: Detect rank jumps, price anomalies
7. **Manifest**: Write run metadata (parameters, DQ results, row counts)

### Stub Data

Pre-generated stub data in `data/raw_stub/` contains 200 items per platform with designed overlap:
- 50 exact-match pairs (same brand + spec)
- 30 variant pairs (same brand, different size)
- 40 similar items (same brand, different product type)
- 80 platform-unique items

Regenerate with: `python _generate_stub_data.py`

## Configuration

- `config/default.yaml` - Full pipeline configuration
- `config/stub.yaml` - Override for stub/offline mode
- Environment variables: `SEA_<SECTION>__<KEY>=value` (e.g. `SEA_INGESTION__USE_STUB=true`)

## Project Structure

```
src/sea_pipeline/
  cli.py              - CLI entry point
  runner.py            - Main orchestrator
  config.py            - Configuration loader
  ingestion/           - Platform adapters + stub loader
  standardisation/     - Brand, spec, unit, currency normalization
  dq/                  - Data quality checks + gates
  export/              - DuckDB writer, Parquet exporter, manifest
  storage/             - Local store, raw cache
  models/              - DuckDB table DDL
```
