# experimental-llm
#
# Common entrypoints. Override defaults on the command line, e.g.:
#   make query TEMPLATES=templates/finance OUT=/tmp/queries

PKG       ?= query-builder
TEMPLATES ?= templates
OUT       ?= $(CURDIR)/queries

.PHONY: help install test query query-dry clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Sync the uv environment (deps + dev tools)
	cd $(PKG) && uv sync

test: ## Run the test suite
	cd $(PKG) && uv run pytest

query: ## Build queries from $(TEMPLATES) into $(OUT)
	cd $(PKG) && uv run query-builder build $(TEMPLATES) --out $(OUT)

query-dry: ## Preview what would be built without writing files
	cd $(PKG) && uv run query-builder build $(TEMPLATES) --out $(OUT) --dry-run

clean: ## Remove generated queries
	rm -rf $(OUT)
