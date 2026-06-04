"""Load and validate query templates.

A template is a YAML file like::

    Query: "Who is the best {broker_type} broker in {area}"
    Subs:
      broker_type: ["real estate", "car"]
      area: ["New York", "Brooklyn"]

The file's stem is the ``prefix`` (``broker``) and its parent directory is the
``category`` (``real-estate``).
"""

from __future__ import annotations

import string
from dataclasses import dataclass
from pathlib import Path

import yaml


class TemplateError(Exception):
    """Raised when a template is missing, malformed, or inconsistent."""


@dataclass(frozen=True)
class Template:
    prefix: str
    category: str
    query: str
    subs: dict[str, list[str]]
    path: Path

    @property
    def placeholders(self) -> set[str]:
        """The set of ``{name}`` fields referenced in the query string."""
        return {
            name
            for _, name, _, _ in string.Formatter().parse(self.query)
            if name
        }

    @classmethod
    def load(cls, path: str | Path) -> "Template":
        path = Path(path)
        if not path.is_file():
            raise TemplateError(f"Template not found: {path}")

        try:
            raw = yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError as exc:
            raise TemplateError(f"Could not parse YAML in {path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise TemplateError(f"Template {path} must be a mapping")

        if "Query" not in raw:
            raise TemplateError(f"Template {path} is missing a 'Query' key")
        query = raw["Query"]
        if not isinstance(query, str) or not query.strip():
            raise TemplateError(f"Template {path} 'Query' must be a non-empty string")

        subs_raw = raw.get("Subs", {}) or {}
        if not isinstance(subs_raw, dict):
            raise TemplateError(f"Template {path} 'Subs' must be a mapping")

        subs: dict[str, list[str]] = {}
        for key, values in subs_raw.items():
            if not isinstance(values, list):
                raise TemplateError(
                    f"Template {path} sub '{key}' must be a list of values"
                )
            if not values:
                raise TemplateError(f"Template {path} sub '{key}' is empty")
            subs[str(key)] = [str(v) for v in values]

        tmpl = cls(
            prefix=path.stem,
            category=path.parent.name,
            query=query,
            subs=subs,
            path=path,
        )
        tmpl._validate()
        return tmpl

    def _validate(self) -> None:
        placeholders = self.placeholders
        sub_keys = set(self.subs)

        missing = placeholders - sub_keys
        if missing:
            raise TemplateError(
                f"Template {self.path}: no substitutions for placeholder(s): "
                f"{', '.join(sorted(missing))}"
            )

        unused = sub_keys - placeholders
        if unused:
            raise TemplateError(
                f"Template {self.path}: substitution(s) never used in query: "
                f"{', '.join(sorted(unused))}"
            )
