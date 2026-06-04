"""query_enqueue: filter constructed queries and fan them out to target models.

Typical library use::

    from query_enqueue import EnqueueConfig, enqueue, load_source_queries, write

    config = EnqueueConfig.load("enqueue.yaml")
    for unit in enqueue(load_source_queries("queries"), config):
        write(unit, out_dir="enqueued_queries")
"""

from .cli import enqueue_all, main
from .config import ConfigError, EnqueueConfig, ModelTarget
from .enqueuer import EnqueuedQuery, enqueue, is_ignored
from .ids import enqueue_id
from .providers import Auth, Provider, ProviderError, ProviderRegistry
from .source import SourceError, SourceQuery, load_source_queries
from .writer import enqueued_path, model_slug, write

__all__ = [
    "EnqueueConfig",
    "ModelTarget",
    "ConfigError",
    "ProviderRegistry",
    "Provider",
    "Auth",
    "ProviderError",
    "SourceQuery",
    "SourceError",
    "EnqueuedQuery",
    "enqueue",
    "is_ignored",
    "load_source_queries",
    "write",
    "enqueued_path",
    "model_slug",
    "enqueue_id",
    "enqueue_all",
    "main",
]

__version__ = "0.1.0"
