"""Deterministic identifiers for enqueued queries."""

from __future__ import annotations

import hashlib

_ID_LENGTH = 16


def enqueue_id(query_id: str, provider: str, model: str) -> str:
    """Return a stable, short hex id for a ``(query, provider, model)`` unit.

    The id is a SHA-256 digest of the constructed ``query_id``, the ``provider``
    name, and the ``model`` id, truncated to ``_ID_LENGTH`` hex chars. Provider
    is included so the same model served by two providers gets distinct ids. The
    same inputs always yield the same id, so re-running the enqueuer is
    idempotent.
    """
    digest = hashlib.sha256(f"{query_id}\x00{provider}\x00{model}".encode("utf-8"))
    return digest.hexdigest()[:_ID_LENGTH]
