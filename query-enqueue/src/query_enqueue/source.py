"""Load constructed queries written by ``query-builder`` from a queries tree.

Each source query lives at ``<root>/<category>/<prefix>/<dir>/query.yaml`` and
looks like::

    query: Who is the best mortgage broker in Chicago
    metadata:
      id: ea227897d0dc8c32
      prefix: broker
      category: real-estate
      ...
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

QUERY_FILENAME = "query.yaml"


class SourceError(Exception):
    """Raised when the queries tree is missing or a query file is malformed."""


@dataclass(frozen=True)
class SourceQuery:
    """A constructed query loaded from disk, ready to be enqueued."""

    id: str
    query: str
    prefix: str
    category: str
    #: Path of the query's directory relative to the queries root, e.g.
    #: ``real-estate/broker/mortgage.chicago.ea22``.
    rel_path: str
    path: Path


def load_source_queries(root: str | Path) -> list[SourceQuery]:
    """Load every ``query.yaml`` under ``root``, sorted by relative path."""
    root = Path(root)
    if not root.is_dir():
        raise SourceError(f"Queries directory not found: {root}")

    queries = [
        _load_one(path, root) for path in sorted(root.rglob(QUERY_FILENAME))
    ]
    return queries


def _load_one(path: Path, root: Path) -> SourceQuery:
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as exc:
        raise SourceError(f"Could not parse YAML in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise SourceError(f"Query {path} must be a mapping")

    query = data.get("query")
    if not isinstance(query, str) or not query.strip():
        raise SourceError(f"Query {path} 'query' must be a non-empty string")

    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        raise SourceError(f"Query {path} is missing a 'metadata' mapping")

    query_id = metadata.get("id")
    if not isinstance(query_id, str) or not query_id:
        raise SourceError(f"Query {path} is missing 'metadata.id'")

    rel_path = path.parent.relative_to(root).as_posix()
    return SourceQuery(
        id=query_id,
        query=query,
        prefix=str(metadata.get("prefix", "")),
        category=str(metadata.get("category", "")),
        rel_path=rel_path,
        path=path,
    )
