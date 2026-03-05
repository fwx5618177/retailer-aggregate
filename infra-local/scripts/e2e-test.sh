#!/bin/bash
set -euo pipefail

# SEA Retailer End-to-End Acceptance Test
# Tests the full pipeline: data ingestion -> matching -> API serving
# Resolves all paths from the mono-repo root.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PY_PIPELINE="$ROOT/data-pipeline/.venv/bin/python"
PY_MATCHING="$ROOT/matching-engine/.venv/bin/python"
PY_DQ="$ROOT/data-pipeline/.venv/bin/python"  # reuse for duckdb queries

PIPELINE_DB="$ROOT/data-pipeline/data/pipeline.duckdb"
API_BASE="http://localhost:8080/api/v1"

echo "============================================"
echo "  SEA Retailer E2E Acceptance Test"
echo "  Root: $ROOT"
echo "============================================"

PASS=0
FAIL=0

check() {
    local desc="$1"
    local result="$2"
    if [ "$result" = "0" ]; then
        echo "  [PASS] $desc"
        PASS=$((PASS + 1))
    else
        echo "  [FAIL] $desc"
        FAIL=$((FAIL + 1))
    fi
}

echo ""
echo "--- Step 1: Run Data Pipeline (Stub) ---"
cd "$ROOT/data-pipeline"
"$PY_PIPELINE" -m sea_pipeline run --config config/default.yaml --config-override config/stub.yaml 2>&1 || true

# Check pipeline output
echo ""
echo "--- Step 2: Verify Pipeline Output ---"

if [ -f "$PIPELINE_DB" ]; then
    check "DuckDB database exists" 0

    # Check top_items
    COUNT=$("$PY_DQ" -c "import duckdb; c=duckdb.connect('$PIPELINE_DB',read_only=True); print(c.execute('SELECT COUNT(*) FROM top_items').fetchone()[0])" 2>/dev/null || echo "0")
    [ "$COUNT" -gt "0" ] && check "top_items has data ($COUNT rows)" 0 || check "top_items has data" 1

    # Check price_snapshots
    COUNT=$("$PY_DQ" -c "import duckdb; c=duckdb.connect('$PIPELINE_DB',read_only=True); print(c.execute('SELECT COUNT(*) FROM price_snapshots').fetchone()[0])" 2>/dev/null || echo "0")
    [ "$COUNT" -gt "0" ] && check "price_snapshots has data ($COUNT rows)" 0 || check "price_snapshots has data" 1

    # Check both platforms
    PLATFORMS=$("$PY_DQ" -c "import duckdb; c=duckdb.connect('$PIPELINE_DB',read_only=True); print(c.execute('SELECT DISTINCT platform FROM top_items ORDER BY platform').fetchall())" 2>/dev/null || echo "[]")
    echo "$PLATFORMS" | grep -q "tiktok" && check "TikTok data present" 0 || check "TikTok data present" 1
    echo "$PLATFORMS" | grep -q "shopee" && check "Shopee data present" 0 || check "Shopee data present" 1
else
    check "DuckDB database exists" 1
fi

echo ""
echo "--- Step 3: Run Matching Engine ---"
cd "$ROOT/matching-engine"
"$PY_MATCHING" -m sea_matching --config config/default.yaml 2>&1 || true

echo ""
echo "--- Step 4: Verify Matching Output ---"

# Check match_map_platform in DuckDB
MATCH_COUNT=$("$PY_DQ" -c "import duckdb; c=duckdb.connect('$PIPELINE_DB',read_only=True); print(c.execute('SELECT COUNT(*) FROM match_map_platform').fetchone()[0])" 2>/dev/null || echo "0")
[ "$MATCH_COUNT" -gt "0" ] && check "match_map_platform has data ($MATCH_COUNT rows)" 0 || check "match_map_platform has data" 1

# Check match type distribution
AUTO=$("$PY_DQ" -c "import duckdb; c=duckdb.connect('$PIPELINE_DB',read_only=True); print(c.execute(\"SELECT COUNT(*) FROM match_map_platform WHERE status='auto_accepted'\").fetchone()[0])" 2>/dev/null || echo "0")
REVIEW=$("$PY_DQ" -c "import duckdb; c=duckdb.connect('$PIPELINE_DB',read_only=True); print(c.execute(\"SELECT COUNT(*) FROM match_map_platform WHERE status='needs_review'\").fetchone()[0])" 2>/dev/null || echo "0")
TOTAL_CLASSIFIED=$((AUTO + REVIEW))
check "Matches classified ($AUTO auto, $REVIEW review)" $([ "$TOTAL_CLASSIFIED" -gt "0" ] && echo 0 || echo 1)

echo ""
echo "--- Step 5: Verify API Endpoints ---"

# Check if API is running
if curl -sf "$API_BASE/../healthz" > /dev/null 2>&1; then
    check "API backend reachable (/healthz)" 0

    # GET /overview
    OVERVIEW=$(curl -sf "$API_BASE/overview" 2>/dev/null || echo "")
    if echo "$OVERVIEW" | grep -q '"event_date"'; then
        check "GET /overview returns data" 0
    else
        check "GET /overview returns data" 1
    fi

    # GET /top-items
    TOP_ITEMS=$(curl -sf "$API_BASE/top-items?page=0&size=5" 2>/dev/null || echo "")
    if echo "$TOP_ITEMS" | grep -q '"items"'; then
        check "GET /top-items returns data" 0
    else
        check "GET /top-items returns data" 1
    fi

    # GET /review-queue
    REVIEW_Q=$(curl -sf "$API_BASE/review-queue?page=0&size=5" 2>/dev/null || echo "")
    if echo "$REVIEW_Q" | grep -q '"items"'; then
        check "GET /review-queue returns data" 0
    else
        check "GET /review-queue returns data" 1
    fi

    # GET /alerts
    ALERTS=$(curl -sf "$API_BASE/alerts?page=0&size=5" 2>/dev/null || echo "")
    if echo "$ALERTS" | grep -q '"items"'; then
        check "GET /alerts returns data" 0
    else
        check "GET /alerts returns data" 1
    fi
else
    echo "  [SKIP] API backend not running -- skipping endpoint checks"
    echo "         Start with: cd $ROOT/api-backend && ./mvnw spring-boot:run -Dspring-boot.run.profiles=local"
fi

echo ""
echo "============================================"
echo "  Results: $PASS passed, $FAIL failed"
echo "============================================"

[ "$FAIL" -eq "0" ] && exit 0 || exit 1
