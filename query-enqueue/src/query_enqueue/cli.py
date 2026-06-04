"""Command-line entrypoint for the query enqueuer.

Usage::

    query-enqueue enqueue QUERIES_DIR [--config enqueue.yaml]
        [--providers providers.yaml] [--out DIR] [--dry-run]

Scans ``QUERIES_DIR`` for ``query.yaml`` files, drops any whose path matches an
``ignore`` glob in the config, and fans the rest out to every model in the
config -- writing one unit per ``(query, model)`` pair under ``--out``. Each
model references a provider defined in the shared ``--providers`` registry; the
registry is validated but its connection details are not written into units.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .config import ConfigError, EnqueueConfig
from .enqueuer import enqueue
from .providers import ProviderError, ProviderRegistry
from .source import SourceError, load_source_queries
from .writer import enqueued_path, write

DEFAULT_CONFIG = "enqueue.yaml"
DEFAULT_PROVIDERS = "providers.yaml"
DEFAULT_OUT = "enqueued_queries"


def enqueue_all(
    queries_dir: str | Path,
    config_path: str | Path = DEFAULT_CONFIG,
    providers_path: str | Path = DEFAULT_PROVIDERS,
    out_dir: str | Path = DEFAULT_OUT,
    dry_run: bool = False,
) -> int:
    """Enqueue every query under ``queries_dir``; return the unit count."""
    registry = ProviderRegistry.load(providers_path)
    config = EnqueueConfig.load(config_path, registry)
    queries = load_source_queries(queries_dir)
    units = enqueue(queries, config)

    for unit in units:
        if dry_run:
            print(f"  would write {enqueued_path(unit, out_dir)}")
        else:
            write(unit, out_dir)

    verb = "would enqueue" if dry_run else "enqueued"
    print(
        f"{verb} {len(units)} units "
        f"({len(queries)} queries x {len(config.models)} models, minus ignored)"
    )
    return len(units)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="query-enqueue")
    sub = parser.add_subparsers(dest="command", required=True)

    enqueue_parser = sub.add_parser("enqueue", help="Enqueue queries for the executor")
    enqueue_parser.add_argument("queries_dir", help="Directory of built queries")
    enqueue_parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG,
        help=f"Enqueue config YAML (default: {DEFAULT_CONFIG})",
    )
    enqueue_parser.add_argument(
        "--providers",
        default=DEFAULT_PROVIDERS,
        help=f"Provider registry YAML (default: {DEFAULT_PROVIDERS})",
    )
    enqueue_parser.add_argument(
        "--out", default=DEFAULT_OUT, help=f"Output directory (default: {DEFAULT_OUT})"
    )
    enqueue_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be enqueued without writing files",
    )

    args = parser.parse_args(argv)

    if args.command == "enqueue":
        try:
            total = enqueue_all(
                args.queries_dir,
                config_path=args.config,
                providers_path=args.providers,
                out_dir=args.out,
                dry_run=args.dry_run,
            )
        except (ProviderError, ConfigError, SourceError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        dest = "(dry run)" if args.dry_run else args.out
        print(f"\nTotal: {total} units -> {dest}")
        return 0

    return 2  # pragma: no cover - argparse enforces a valid command


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
