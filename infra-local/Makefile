.PHONY: help deps up down mvp-stub mvp-live pipeline pipeline-stub matching api frontend streamlit e2e test-all clean start-all

# Resolve paths relative to the mono-repo root
ROOT         := $(realpath $(CURDIR)/..)
PY_PIPELINE  := $(ROOT)/data-pipeline/.venv/bin/python
PY_MATCHING  := $(ROOT)/matching-engine/.venv/bin/python
PY_STREAMLIT := $(ROOT)/app-mvp/.venv/bin/streamlit

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-20s %s\n", $$1, $$2}'

deps:  ## Start databases only (ClickHouse + Postgres + Keycloak)
	docker compose -f docker-compose.deps.yaml up -d

up:  ## Start full stack (all services)
	docker compose up -d

down:  ## Stop all containers
	docker compose down

mvp-stub:  ## Run full MVP with stub data (no network required)
	@echo "=== SEA Retailer MVP (Stub Mode) ==="
	@echo "Step 1: Running data pipeline (stub)..."
	cd $(ROOT)/data-pipeline && $(PY_PIPELINE) -m sea_pipeline run \
		--config config/default.yaml \
		--config-override config/stub.yaml
	@echo "Step 2: Running matching engine..."
	cd $(ROOT)/matching-engine && $(PY_MATCHING) -m sea_matching \
		--config config/default.yaml
	@echo "=== Pipeline complete ==="
	@echo "To view results:"
	@echo "  API:       make api"
	@echo "  Frontend:  make frontend"
	@echo "  Streamlit: make streamlit"

mvp-live:  ## Run full MVP with live data (best-effort, falls back to stub)
	@echo "=== SEA Retailer MVP (Live Mode) ==="
	@echo "Step 1: Running data pipeline (live)..."
	cd $(ROOT)/data-pipeline && $(PY_PIPELINE) -m sea_pipeline run \
		--config config/default.yaml
	@echo "Step 2: Running matching engine..."
	cd $(ROOT)/matching-engine && $(PY_MATCHING) -m sea_matching \
		--config config/default.yaml
	@echo "=== Pipeline complete ==="

pipeline:  ## Run data pipeline only
	cd $(ROOT)/data-pipeline && $(PY_PIPELINE) -m sea_pipeline run --config config/default.yaml

pipeline-stub:  ## Run data pipeline with stub data
	cd $(ROOT)/data-pipeline && $(PY_PIPELINE) -m sea_pipeline run \
		--config config/default.yaml --config-override config/stub.yaml

matching:  ## Run matching engine only
	cd $(ROOT)/matching-engine && $(PY_MATCHING) -m sea_matching --config config/default.yaml

api:  ## Start API backend (local profile)
	cd $(ROOT)/api-backend && ./mvnw spring-boot:run -Dspring-boot.run.profiles=local

frontend:  ## Start web frontend dev server
	cd $(ROOT)/web-frontend && npm run dev

streamlit:  ## Start Streamlit app
	cd $(ROOT)/app-mvp/src/app && $(PY_STREAMLIT) run main.py --server.port 8501

e2e:  ## Run end-to-end acceptance test
	./scripts/e2e-test.sh

test-all:  ## Run all tests across repos
	@echo "=== Data Pipeline Tests ==="
	cd $(ROOT)/data-pipeline && $(PY_PIPELINE) -m pytest tests/ -v
	@echo "=== Matching Engine Tests ==="
	cd $(ROOT)/matching-engine && $(PY_MATCHING) -m pytest tests/ -v
	@echo "=== API Backend Tests ==="
	cd $(ROOT)/api-backend && ./mvnw test
	@echo "=== All tests complete ==="

start-all: mvp-stub  ## Run pipeline+matching, then start API, frontend, and Streamlit
	@echo "=== Starting all services ==="
	@echo "Starting API backend (port 8080)..."
	cd $(ROOT)/api-backend && ./mvnw spring-boot:run -Dspring-boot.run.profiles=local &
	@sleep 5
	@echo "Starting web frontend (port 3000)..."
	cd $(ROOT)/web-frontend && npm run dev &
	@echo "Starting Streamlit (port 8501)..."
	cd $(ROOT)/app-mvp/src/app && $(PY_STREAMLIT) run main.py --server.port 8501 &
	@echo "=== All services started ==="
	@echo "  API:       http://localhost:8080"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Streamlit: http://localhost:8501"
	@echo "Press Ctrl+C to stop all services"
	@wait

clean:  ## Remove all data and containers
	docker compose down -v 2>/dev/null || true
	docker compose -f docker-compose.deps.yaml down -v 2>/dev/null || true
	rm -rf $(ROOT)/data-pipeline/data/pipeline.duckdb
	rm -rf $(ROOT)/data-pipeline/data/serving/
	rm -rf $(ROOT)/data-pipeline/data/raw_cache/
	rm -rf $(ROOT)/matching-engine/data/matching_output/
	rm -rf $(ROOT)/matching-engine/reports/
	@echo "Cleaned all local data"
