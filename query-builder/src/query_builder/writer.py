"""Persist constructed queries to ``<out_dir>/<prefix>/<id>/query.yaml``."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import yaml

from .builder import ConstructedQuery

QUERY_FILENAME = "query.yaml"

#: Max length of each camelCased substitution in a directory name.
_SUB_MAX_LEN = 10
#: Number of leading id characters appended to a directory name.
_ID_SUFFIX_LEN = 4


def _camel(value: str) -> str:
    """camelCase a value: ``"real estate"`` -> ``"realEstate"``."""
    words = [w for w in re.split(r"[^a-zA-Z0-9]+", value) if w]
    if not words:
        return ""
    head, *tail = words
    return head.lower() + "".join(w[:1].upper() + w[1:].lower() for w in tail)


def query_dirname(query: ConstructedQuery) -> str:
    """Human-readable directory name for a query.

    Built from the substitution values in template order, each camelCased and
    capped at ``_SUB_MAX_LEN`` chars, joined by ``.`` and suffixed with the
    first ``_ID_SUFFIX_LEN`` chars of the id to keep names distinct -- e.g.
    ``realEstate.newYork.dead``.
    """
    parts = [_camel(v)[:_SUB_MAX_LEN] for v in query.substitutions.values()]
    parts.append(query.id[:_ID_SUFFIX_LEN])
    return ".".join(parts)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def query_path(query: ConstructedQuery, out_dir: str | Path) -> Path:
    """Return the path a query would be written to (without writing it).

    The layout mirrors the template's location, with a readable leaf directory:
    ``<out_dir>/<category>/<prefix>/<subs>.<id4>/query.yaml`` (e.g. a
    ``finance/stocks.yaml`` template writes under ``<out_dir>/finance/stocks/``).
    """
    return (
        Path(out_dir)
        / query.category
        / query.prefix
        / query_dirname(query)
        / QUERY_FILENAME
    )


def write(
    query: ConstructedQuery,
    out_dir: str | Path,
    now: Callable[[], str] = _utcnow_iso,
) -> Path:
    """Write ``query`` to disk and return the path.

    The output is a single YAML document with the resolved query at the top
    level and everything else nested under ``metadata``. Writes are idempotent:
    re-running with the same query preserves the original ``created_at`` so the
    file content stays stable across runs.
    """
    path = query_path(query, out_dir)
    path.parent.mkdir(parents=True, exist_ok=True)

    created_at = _existing_created_at(path) or now()

    document = {
        "query": query.query,
        "metadata": {
            "id": query.id,
            "prefix": query.prefix,
            "category": query.category,
            "template_query": query.template_query,
            "substitutions": dict(query.substitutions),
            "created_at": created_at,
        },
    }

    path.write_text(
        yaml.safe_dump(document, sort_keys=False, allow_unicode=True)
    )
    return path


def _existing_created_at(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError:
        return None
    return (data.get("metadata") or {}).get("created_at")
