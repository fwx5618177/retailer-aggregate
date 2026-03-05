.PHONY: run run-stub test lint clean

run:
	python -m sea_pipeline run --config config/default.yaml

run-stub:
	python -m sea_pipeline run --config config/default.yaml --config-override config/stub.yaml

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/

clean:
	rm -rf data/pipeline.duckdb data/serving/ data/raw_cache/
