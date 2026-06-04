"""Command-line entrypoint for the query builder.

Usage::

    query-builder build TEMPLATE [TEMPLATE ...] [--out DIR] [--dry-run]

Each ``TEMPLATE`` may be a single ``.yaml`` template file or a directory, which
is walked recursively for ``*.yaml`` templates.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .builder import build
from .template import Template, TemplateError
from .writer import query_path, write

DEFAULT_OUT = "queries"


def _resolve_template_files(paths: Sequence[str]) -> list[Path]:
    """Expand the given paths into a sorted, de-duplicated list of yaml files."""
    files: list[Path] = []
    seen: set[Path] = set()
    for raw in paths:
        path = Path(raw)
        if not path.exists():
            raise TemplateError(f"Path not found: {path}")
        candidates = (
            sorted(path.rglob("*.yaml")) if path.is_dir() else [path]
        )
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(candidate)
    return files


def build_paths(
    paths: Sequence[str],
    out_dir: str | Path = DEFAULT_OUT,
    dry_run: bool = False,
) -> int:
    """Build every template found under ``paths``; return the query count."""
    total = 0
    for template_file in _resolve_template_files(paths):
        template = Template.load(template_file)
        queries = build(template)
        for query in queries:
            if dry_run:
                print(f"  would write {query_path(query, out_dir)}")
            else:
                write(query, out_dir)
        verb = "would build" if dry_run else "built"
        print(f"{verb} {len(queries)} queries from {template.category}/{template.prefix}")
        total += len(queries)
    return total


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="query-builder")
    sub = parser.add_subparsers(dest="command", required=True)

    build_parser = sub.add_parser("build", help="Build queries from templates")
    build_parser.add_argument(
        "paths", nargs="+", help="Template .yaml file(s) or directory(ies)"
    )
    build_parser.add_argument(
        "--out", default=DEFAULT_OUT, help=f"Output directory (default: {DEFAULT_OUT})"
    )
    build_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be built without writing files",
    )

    args = parser.parse_args(argv)

    if args.command == "build":
        try:
            total = build_paths(args.paths, out_dir=args.out, dry_run=args.dry_run)
        except TemplateError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        dest = "(dry run)" if args.dry_run else args.out
        print(f"\nTotal: {total} queries -> {dest}")
        return 0

    return 2  # pragma: no cover - argparse enforces a valid command


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
