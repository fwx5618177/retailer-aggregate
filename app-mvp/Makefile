.PHONY: run run-stub help

run:  ## Run Streamlit app
	cd src/app && streamlit run main.py --server.port 8501

help:  ## Show help
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-15s %s\n", $$1, $$2}'
