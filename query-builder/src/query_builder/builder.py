"""Expand a template into concrete queries via the cartesian product of subs."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from .ids import query_id
from .template import Template


@dataclass(frozen=True)
class ConstructedQuery:
    """A single resolved query plus the metadata describing how it was built."""

    id: str
    query: str
    prefix: str
    category: str
    template_query: str
    substitutions: dict[str, str]


def build(template: Template) -> list[ConstructedQuery]:
    """Return one :class:`ConstructedQuery` per combination of substitutions.

    The combinations are the cartesian product of every value list in
    ``template.subs``, taken in the key order of that mapping. The output order
    is deterministic for a given template.
    """
    keys = list(template.subs)
    value_lists = [template.subs[k] for k in keys]

    queries: list[ConstructedQuery] = []
    for combo in product(*value_lists):
        substitutions = dict(zip(keys, combo))
        resolved = template.query.format(**substitutions)
        queries.append(
            ConstructedQuery(
                id=query_id(template.prefix, resolved),
                query=resolved,
                prefix=template.prefix,
                category=template.category,
                template_query=template.query,
                substitutions=substitutions,
            )
        )
    return queries
