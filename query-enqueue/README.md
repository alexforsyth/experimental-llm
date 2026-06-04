# Query Enqueue

Enqueue constructed queries (built by `query-builder`) for the executor.

Given a `queries/` tree, an enqueue config, and a provider registry, the
enqueuer:

- skips any query whose directory path matches an `ignore` glob, and
- fans every remaining query out to each target model in `models`,

writing one enqueued unit per `(query, model)` pair to
`enqueued_queries/<category>/<prefix>/<query>/<provider>.<model>/query.yaml`.
Each unit is a future queue message: it references its target provider + model
and back-references the constructed query.

## Provider registry

Providers live in a shared `providers.yaml` (by convention at the repo root) —
the single source of truth read by both the enqueuer (to validate references)
and the executor/workers (to resolve connection details at run time).

```yaml
# providers.yaml
providers:
  anthropic:
    type: anthropic                 # adapter/wire format (defaults to the key)
    base_url: https://api.anthropic.com
    auth: {type: env, var: ANTHROPIC_API_KEY}
  local:
    type: openai                    # OpenAI-compatible (ollama, vLLM, ...)
    base_url: http://localhost:11434/v1
    auth: {type: none}
  bedrock:
    region: us-east-1
    auth: {type: aws, profile: default}
```

`auth` types: `env` (`var:` names an env var), `aws` (standard credential chain,
optional `profile`/`region`), `none`. A secret is never stored — only referenced.

## Enqueue config

```yaml
# enqueue.yaml
models:
  - name: claude-opus-4-8           # the provider's model id
    provider: anthropic             # must exist in providers.yaml
    max_tokens: 1024                # extra keys pass through to the executor
    temperature: 1.0
  - name: llama3.1:8b
    provider: local
ignore:
  - "finance/**"                    # skip a whole category
  - "real-estate/broker/car.*"      # skip specific queries
```

Each model needs a `name` and a `provider`; any other keys are per-call options.
Globs match each query's path relative to the queries root (e.g.
`real-estate/broker/mortgage.chicago.ea22`), using `fnmatch` semantics where
`*` also matches `/`.

## Enqueued unit

```yaml
# enqueued_queries/real-estate/broker/mortgage.chicago.ea22/anthropic.claude-opus-4-8/query.yaml
query: Who is the best mortgage broker in Chicago
target:
  provider: anthropic               # reference; resolved via providers.yaml
  name: claude-opus-4-8
  max_tokens: 1024
metadata:
  enqueue_id: ...
  query_id: ea227897d0dc8c32
  prefix: broker
  category: real-estate
  source: real-estate/broker/mortgage.chicago.ea22/query.yaml
  enqueued_at: '...'
```

No `base_url`, `region`, or `auth` is written into a unit — only the provider
name. A worker resolves the rest from `providers.yaml`.

## CLI

```
query-enqueue enqueue QUERIES_DIR \
    --config enqueue.yaml --providers providers.yaml --out enqueued_queries [--dry-run]
```
