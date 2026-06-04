# experimental-llm
#
# Common entrypoints. Override defaults on the command line, e.g.:
#   make query TEMPLATES=templates/finance OUT=/tmp/queries
#   make enqueue ENQUEUE_CONFIG=/tmp/enqueue.yaml

PKG            ?= query-builder
ENQUEUE_PKG    ?= query-enqueue
TEMPLATES      ?= templates
OUT            ?= $(CURDIR)/queries
ENQUEUE_CONFIG ?= $(CURDIR)/enqueue.yaml
PROVIDERS      ?= $(CURDIR)/providers.yaml
ENQUEUED_OUT   ?= $(CURDIR)/enqueued_queries

.PHONY: help install test query query-dry enqueue enqueue-dry clean clean-enqueued

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Sync the uv environments (deps + dev tools) for all packages
	cd $(PKG) && uv sync
	cd $(ENQUEUE_PKG) && uv sync

test: ## Run the test suites for all packages
	cd $(PKG) && uv run pytest
	cd $(ENQUEUE_PKG) && uv run pytest

query: ## Build queries from $(TEMPLATES) into $(OUT)
	cd $(PKG) && uv run query-builder build $(TEMPLATES) --out $(OUT)

query-dry: ## Preview what would be built without writing files
	cd $(PKG) && uv run query-builder build $(TEMPLATES) --out $(OUT) --dry-run

enqueue: ## Enqueue queries from $(OUT) into $(ENQUEUED_OUT) using $(ENQUEUE_CONFIG)
	cd $(ENQUEUE_PKG) && uv run query-enqueue enqueue $(OUT) --config $(ENQUEUE_CONFIG) --providers $(PROVIDERS) --out $(ENQUEUED_OUT)

enqueue-dry: ## Preview what would be enqueued without writing files
	cd $(ENQUEUE_PKG) && uv run query-enqueue enqueue $(OUT) --config $(ENQUEUE_CONFIG) --providers $(PROVIDERS) --out $(ENQUEUED_OUT) --dry-run

clean: ## Remove generated queries
	rm -rf $(OUT)

clean-enqueued: ## Remove enqueued queries
	rm -rf $(ENQUEUED_OUT)
