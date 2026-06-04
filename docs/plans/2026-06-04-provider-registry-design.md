# Provider/Endpoint Registry — Design

Date: 2026-06-04
Component: `query-enqueue` (plus a forward contract for `query-executor`)

## Problem

Model targets need to point at different providers — local, AWS Bedrock,
Anthropic, OpenAI, etc. Today a `ModelTarget` is just `{name, endpoint, options}`,
which conflates "which model" with "how to reach it" and can't express
provider-specific concerns (wire format, auth style, region). We want a way to
declare providers once and have many models reference them, without baking
secrets or connection details into the enqueued queue messages.

## Decisions

1. **Named provider enum.** A model selects a provider by name; each provider has
   a `type` that selects the executor's adapter (`anthropic` / `openai` /
   `bedrock` / ...). The enqueuer does **not** hard-code the type enum — unknown
   types pass through, since the executor owns the adapter set.
2. **Shared registry at the repo root.** Providers live in a standalone
   `providers.yaml` at the repo root — the single source of truth read by both
   the enqueuer (for validation) and the future executor/workers (for
   resolution). `enqueue.yaml` keeps only enqueue policy and references providers
   by name.
3. **Pluggable auth, no secrets on disk.** Each provider has an `auth` block with
   a `type` (`env` / `aws` / `none`) and type-specific fields. Only references are
   stored (e.g. an env var name); never a raw secret.
4. **Reference-only units.** Each enqueued unit carries `target.provider` (a
   name) — not the resolved connection details. Workers resolve the provider via
   the shared `providers.yaml` at run time. Lean messages, one source of truth.

## Config schema

`providers.yaml` (repo root):

```yaml
providers:
  anthropic:
    type: anthropic                 # defaults to the registry key if omitted
    base_url: https://api.anthropic.com
    auth: {type: env, var: ANTHROPIC_API_KEY}
  local:
    type: openai                    # OpenAI-compatible wire format
    base_url: http://localhost:11434/v1
    auth: {type: none}
  bedrock:
    type: bedrock
    region: us-east-1
    auth: {type: aws, profile: default}
```

`enqueue.yaml`:

```yaml
models:
  - name: claude-opus-4-8           # provider's model id
    provider: anthropic             # must exist in providers.yaml
    max_tokens: 1024                # per-call options, passed through
  - name: llama3.1:8b
    provider: local
ignore: []
```

## Validation

New `providers.py`:

- `ProviderRegistry.load(path)` — file must exist and contain a `providers:`
  mapping, else `ProviderError`.
- Each provider parses into a `Provider{name, type, base_url, region, auth,
  options}`; `type` defaults to the key.
- `auth` parses into `Auth{type, params}`: `env` requires `var`; `aws` allows
  optional `profile`/`region`; `none` takes nothing; unknown `auth.type` errors
  (typo guard).
- `type` is **not** constrained to an enum at enqueue time.

Config join — `EnqueueConfig.load(enqueue_path, registry)`:

- Each model requires `name` (str) and `provider` (str). String-shorthand models
  are dropped (provider is now mandatory, so the mapping form is required).
- **Referential integrity:** every `model.provider` must be a key in the
  registry, else `ConfigError` naming the bad model and the known providers.
  Runs before any unit is written (fail fast).

## Enqueued unit payload

```yaml
# enqueued_queries/<category>/<prefix>/<query>/<provider>.<model>/query.yaml
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

No `base_url`, `region`, or `auth` in the unit — only the provider name.

## Identity & layout (collision-safety)

One model id can be served by multiple providers (`claude-opus-4-8` via
`anthropic` and `bedrock`), so provider factors into identity:

- `enqueue_id = sha256(query_id, provider, name)` (was `(query_id, name)`).
- Path leaf becomes `<provider>.<model-slug>` (e.g. `anthropic.claude-opus-4-8`).

`ModelTarget` becomes `{provider, name, options}` (drops `endpoint`);
`to_dict()` emits `provider`, `name`, then flattened options.

## CLI / wiring

- `query-enqueue enqueue QUERIES_DIR --config enqueue.yaml --providers providers.yaml --out DIR [--dry-run]`.
- `--providers` defaults to `providers.yaml` (cwd-relative); the Makefile passes
  the repo-root absolute path.
- Errors raised: `ProviderError`, `ConfigError`, `SourceError` → exit 1 with a
  clear message.

## Executor contract (sketch — not built here)

A worker reads a unit → looks up `target.provider` in `providers.yaml` → builds
the adapter for that `type` → resolves `auth` from env / AWS credential chain →
calls the model `name` with `options`.

## Out of scope / YAGNI

- No executor adapters (separate component).
- No `type` enum enforcement, no soft warnings (can add later).
- No multi-file provider includes; one `providers.yaml`.
