"""Load and validate the enqueue config (enqueue policy).

The config is a YAML file like::

    models:
      - name: claude-opus-4-8       # the provider's model id
        provider: anthropic         # must reference a provider in the registry
        max_tokens: 1024            # extra keys pass through to the executor
      - name: llama3.1:8b
        provider: local
    ignore:
      - "finance/**"
      - "real-estate/broker/car.*"

``models`` is the list of target models every enqueued query fans out to; each
references a provider defined in the shared registry (see
:mod:`query_enqueue.providers`). ``ignore`` is an optional list of globs; any
query whose path matches one is skipped. Connection details (base URL, auth,
region) live on the provider, not here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .providers import ProviderRegistry


class ConfigError(Exception):
    """Raised when the enqueue config is missing, malformed, or inconsistent."""


@dataclass(frozen=True)
class ModelTarget:
    """A model to enqueue: its id, the provider that serves it, and call params."""

    name: str
    provider: str
    #: Per-call options (e.g. max_tokens, temperature), passed through verbatim.
    options: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def parse(cls, raw: Any) -> "ModelTarget":
        if not isinstance(raw, dict):
            raise ConfigError(
                f"model entry must be a mapping with 'name' and 'provider', got "
                f"{type(raw).__name__}"
            )

        name = raw.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ConfigError(f"model entry is missing a 'name': {raw!r}")

        provider = raw.get("provider")
        if not isinstance(provider, str) or not provider.strip():
            raise ConfigError(f"model '{name}' is missing a 'provider'")

        options = {k: v for k, v in raw.items() if k not in ("name", "provider")}
        return cls(name=name, provider=provider, options=options)

    def to_dict(self) -> dict[str, Any]:
        """Flatten to the unit form: ``provider``, ``name``, then options."""
        result: dict[str, Any] = {"provider": self.provider, "name": self.name}
        result.update(self.options)
        return result


@dataclass(frozen=True)
class EnqueueConfig:
    models: list[ModelTarget]
    ignore: list[str]

    @classmethod
    def load(cls, path: str | Path, registry: ProviderRegistry) -> "EnqueueConfig":
        path = Path(path)
        if not path.is_file():
            raise ConfigError(f"Config not found: {path}")

        try:
            raw = yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError as exc:
            raise ConfigError(f"Could not parse YAML in {path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise ConfigError(f"Config {path} must be a mapping")

        models_raw = raw.get("models")
        if not isinstance(models_raw, list):
            raise ConfigError(f"Config {path} 'models' must be a list")
        if not models_raw:
            raise ConfigError(f"Config {path} 'models' is empty")
        models = [ModelTarget.parse(m) for m in models_raw]

        for model in models:
            if model.provider not in registry:
                known = ", ".join(sorted(registry.providers)) or "(none)"
                raise ConfigError(
                    f"model '{model.name}' references unknown provider "
                    f"'{model.provider}'; known providers: {known}"
                )

        ignore_raw = raw.get("ignore", []) or []
        if not isinstance(ignore_raw, list):
            raise ConfigError(f"Config {path} 'ignore' must be a list")
        ignore = [str(g) for g in ignore_raw]

        return cls(models=models, ignore=ignore)
