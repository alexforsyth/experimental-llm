"""Turn source queries into enqueued units: filter by glob, fan out to models.

Each non-ignored :class:`~query_enqueue.source.SourceQuery` is expanded into one
:class:`EnqueuedQuery` per target model. The output order is deterministic:
queries in input order, models in config order.
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch

from .config import EnqueueConfig, ModelTarget
from .ids import enqueue_id
from .source import SourceQuery


@dataclass(frozen=True)
class EnqueuedQuery:
    """A single ``(query, model)`` unit of work, ready to write to the queue."""

    enqueue_id: str
    model: ModelTarget
    query_id: str
    query: str
    prefix: str
    category: str
    #: The source query's path relative to the queries root.
    source: str


def is_ignored(rel_path: str, ignore: list[str]) -> bool:
    """Return ``True`` if ``rel_path`` matches any ``ignore`` glob.

    Patterns are matched with :func:`fnmatch.fnmatch`, so ``*`` also matches
    ``/`` (e.g. ``finance/**`` and ``finance/*`` both match a nested query).
    """
    return any(fnmatch(rel_path, pattern) for pattern in ignore)


def enqueue(
    queries: list[SourceQuery], config: EnqueueConfig
) -> list[EnqueuedQuery]:
    """Filter ``queries`` by the config's ignore globs and fan out to models."""
    enqueued: list[EnqueuedQuery] = []
    for query in queries:
        if is_ignored(query.rel_path, config.ignore):
            continue
        for model in config.models:
            enqueued.append(
                EnqueuedQuery(
                    enqueue_id=enqueue_id(query.id, model.provider, model.name),
                    model=model,
                    query_id=query.id,
                    query=query.query,
                    prefix=query.prefix,
                    category=query.category,
                    source=query.rel_path,
                )
            )
    return enqueued
