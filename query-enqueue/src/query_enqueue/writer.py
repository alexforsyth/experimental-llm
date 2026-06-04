"""Persist enqueued queries to ``<out_dir>/<source>/<model>/query.yaml``.

The layout mirrors the source query's path under the queries root, with the
target model as the leaf directory, so the two models for one query never
collide:

    enqueued_queries/real-estate/broker/mortgage.chicago.ea22/
        claude-opus-4-8/query.yaml
        claude-sonnet-4-6/query.yaml

Each file is one future queue message.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import yaml

from .enqueuer import EnqueuedQuery
from .source import QUERY_FILENAME

ENQUEUED_FILENAME = "query.yaml"


def model_slug(model: str) -> str:
    """Filesystem-safe directory name for a model id.

    Keeps alphanumerics, ``.``, ``_`` and ``-``; collapses any other run of
    characters into a single ``-`` (e.g. ``vendor/model:v1`` -> ``vendor-model-v1``).
    """
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", model)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def enqueued_path(enq: EnqueuedQuery, out_dir: str | Path) -> Path:
    """Return the path ``enq`` would be written to (without writing it).

    The leaf is ``<provider>.<model>`` so the same model served by two providers
    never collides.
    """
    leaf = f"{model_slug(enq.model.provider)}.{model_slug(enq.model.name)}"
    return Path(out_dir) / enq.source / leaf / ENQUEUED_FILENAME


def write(
    enq: EnqueuedQuery,
    out_dir: str | Path,
    now: Callable[[], str] = _utcnow_iso,
) -> Path:
    """Write ``enq`` to disk and return the path.

    Writes are idempotent: re-running with the same enqueued query preserves the
    original ``enqueued_at`` so the file content stays stable across runs.
    """
    path = enqueued_path(enq, out_dir)
    path.parent.mkdir(parents=True, exist_ok=True)

    enqueued_at = _existing_enqueued_at(path) or now()

    document = {
        "query": enq.query,
        "target": enq.model.to_dict(),
        "metadata": {
            "enqueue_id": enq.enqueue_id,
            "query_id": enq.query_id,
            "prefix": enq.prefix,
            "category": enq.category,
            "source": f"{enq.source}/{QUERY_FILENAME}",
            "enqueued_at": enqueued_at,
        },
    }

    path.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True))
    return path


def _existing_enqueued_at(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError:
        return None
    return (data.get("metadata") or {}).get("enqueued_at")
