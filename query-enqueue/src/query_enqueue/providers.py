"""Load and validate the shared provider registry.

The registry is a standalone YAML file (by convention ``providers.yaml`` at the
repo root) read by both the enqueuer and the executor/workers::

    providers:
      anthropic:
        type: anthropic                 # defaults to the key if omitted
        base_url: https://api.anthropic.com
        auth: {type: env, var: ANTHROPIC_API_KEY}
      local:
        type: openai
        base_url: http://localhost:11434/v1
        auth: {type: none}
      bedrock:
        region: us-east-1
        auth: {type: aws, profile: default}

Each provider's ``type`` selects the executor's adapter; the enqueuer does not
constrain it to a fixed enum. ``auth`` only ever references a secret (e.g. an
env var name) -- it never holds one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

#: Provider keys parsed into dedicated fields; everything else becomes options.
_KNOWN_KEYS = ("type", "base_url", "region", "auth")


class ProviderError(Exception):
    """Raised when the provider registry is missing or malformed."""


@dataclass(frozen=True)
class Auth:
    """How to authenticate to a provider -- a reference, never a raw secret."""

    type: str
    params: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def parse(cls, raw: Any, provider: str) -> "Auth":
        if raw is None:
            return cls(type="none")
        if not isinstance(raw, dict):
            raise ProviderError(f"provider '{provider}' auth must be a mapping")

        auth_type = raw.get("type")
        if not isinstance(auth_type, str) or not auth_type:
            raise ProviderError(f"provider '{provider}' auth is missing a 'type'")
        params = {k: v for k, v in raw.items() if k != "type"}

        if auth_type == "env":
            if not params.get("var"):
                raise ProviderError(
                    f"provider '{provider}' auth type 'env' requires a 'var'"
                )
        elif auth_type in ("aws", "none"):
            pass
        else:
            raise ProviderError(
                f"provider '{provider}' has unknown auth type '{auth_type}' "
                "(expected env, aws, or none)"
            )

        return cls(type=auth_type, params=params)


@dataclass(frozen=True)
class Provider:
    """A place/way to reach models: wire-format ``type`` plus connection info."""

    name: str
    type: str
    base_url: str | None = None
    region: str | None = None
    auth: Auth = field(default_factory=lambda: Auth(type="none"))
    #: Any keys other than type/base_url/region/auth, passed through verbatim.
    options: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def parse(cls, name: str, raw: Any) -> "Provider":
        if not isinstance(raw, dict):
            raise ProviderError(f"provider '{name}' must be a mapping")

        provider_type = raw.get("type", name)
        if not isinstance(provider_type, str) or not provider_type:
            raise ProviderError(f"provider '{name}' type must be a non-empty string")

        base_url = raw.get("base_url")
        if base_url is not None and not isinstance(base_url, str):
            raise ProviderError(f"provider '{name}' base_url must be a string")

        region = raw.get("region")
        if region is not None and not isinstance(region, str):
            raise ProviderError(f"provider '{name}' region must be a string")

        auth = Auth.parse(raw.get("auth"), name)
        options = {k: v for k, v in raw.items() if k not in _KNOWN_KEYS}

        return cls(
            name=name,
            type=provider_type,
            base_url=base_url,
            region=region,
            auth=auth,
            options=options,
        )


@dataclass(frozen=True)
class ProviderRegistry:
    providers: dict[str, Provider]

    def __contains__(self, name: str) -> bool:
        return name in self.providers

    def get(self, name: str) -> Provider:
        try:
            return self.providers[name]
        except KeyError:
            known = ", ".join(sorted(self.providers)) or "(none)"
            raise ProviderError(
                f"unknown provider '{name}'; known providers: {known}"
            ) from None

    @classmethod
    def load(cls, path: str | Path) -> "ProviderRegistry":
        path = Path(path)
        if not path.is_file():
            raise ProviderError(f"Provider registry not found: {path}")

        try:
            raw = yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError as exc:
            raise ProviderError(f"Could not parse YAML in {path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise ProviderError(f"Registry {path} must be a mapping")

        providers_raw = raw.get("providers")
        if not isinstance(providers_raw, dict):
            raise ProviderError(f"Registry {path} must contain a 'providers' mapping")

        providers = {
            name: Provider.parse(name, spec) for name, spec in providers_raw.items()
        }
        return cls(providers=providers)
