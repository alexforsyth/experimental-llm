"""Persist constructed queries to ``<out_dir>/<prefix>/<id>/query.yaml``."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import yaml

from .builder import ConstructedQuery

QUERY_FILENAME = "query.yaml"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def query_path(query: ConstructedQuery, out_dir: str | Path) -> Path:
    """Return the path a query would be written to (without writing it)."""
    return Path(out_dir) / query.prefix / query.id / QUERY_FILENAME


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
