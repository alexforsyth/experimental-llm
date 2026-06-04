"""Deterministic identifiers for constructed queries."""

from __future__ import annotations

import hashlib

_ID_LENGTH = 16


def query_id(prefix: str, resolved_query: str) -> str:
    """Return a stable, short hex id for a resolved query.

    The id is a SHA-256 digest of ``prefix`` and ``resolved_query`` truncated
    to ``_ID_LENGTH`` hex chars. The same inputs always yield the same id, so
    re-running the builder is idempotent.
    """
    digest = hashlib.sha256(f"{prefix}\x00{resolved_query}".encode("utf-8"))
    return digest.hexdigest()[:_ID_LENGTH]
