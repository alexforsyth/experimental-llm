"""query_builder: build LLM prompt queries from YAML templates.

Typical library use::

    from query_builder import Template, build, write

    template = Template.load("templates/real-estate/broker.yaml")
    for query in build(template):
        write(query, out_dir="queries")
"""

from .builder import ConstructedQuery, build
from .cli import build_paths, main
from .ids import query_id
from .template import Template, TemplateError
from .writer import query_path, write

__all__ = [
    "Template",
    "TemplateError",
    "ConstructedQuery",
    "build",
    "write",
    "query_path",
    "query_id",
    "build_paths",
    "main",
]

__version__ = "0.1.0"
