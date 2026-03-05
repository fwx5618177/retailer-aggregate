.PHONY: run test lint clean

run:  ## Run matching engine
	python -m sea_matching run --config config/default.yaml

test:  ## Run tests
	pytest tests/ -v

lint:  ## Run linter
	ruff check src/ tests/

clean:  ## Clean output files
	rm -rf data/matching_output/ reports/
