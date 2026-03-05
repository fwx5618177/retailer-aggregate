# app-mvp

Streamlit-based internal demo application for the SEA Retailer Top Selling Intelligence platform.

## Pages

1. **Overview** - KPI dashboard with charts (overlap, price bands, top brands)
2. **Top Items** - Filterable table of top-selling items across platforms
3. **Alerts & Opportunities** - Alert cards with severity, type, and suggested actions
4. **Review Queue** - Side-by-side comparison for matching pair review
5. **Run Pipeline** - Trigger pipeline + matching runs from the UI

## Usage

```bash
# Install dependencies
pip install -e .

# Run the app
cd src/app && streamlit run main.py

# Or use Makefile
make run
```

## Data Source

Reads directly from `../data-pipeline/data/pipeline.duckdb`. Run the data pipeline first to populate data.

## Demo

See `demo/demo_script.md` for a guided demo walkthrough covering two key stories:
1. TikTok brand explosion / opportunity discovery
2. Cross-platform price anomaly detection
