import pytest

from query_enqueue.source import SourceError, load_source_queries

QUERY_YAML = (
    "query: Who is the best mortgage broker in Chicago\n"
    "metadata:\n"
    "  id: ea227897d0dc8c32\n"
    "  prefix: broker\n"
    "  category: real-estate\n"
    "  template_query: Who is the best {broker_type} broker in {area}\n"
    "  substitutions:\n"
    "    broker_type: mortgage\n"
    "    area: Chicago\n"
    "  created_at: '2026-06-04T20:54:58+00:00'\n"
)


def write_query(root, rel, text=QUERY_YAML):
    path = root / rel / "query.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_loads_query_fields(tmp_path):
    write_query(tmp_path, "real-estate/broker/mortgage.chicago.ea22")
    (sq,) = load_source_queries(tmp_path)
    assert sq.id == "ea227897d0dc8c32"
    assert sq.query == "Who is the best mortgage broker in Chicago"
    assert sq.prefix == "broker"
    assert sq.category == "real-estate"


def test_rel_path_is_relative_to_root(tmp_path):
    write_query(tmp_path, "real-estate/broker/mortgage.chicago.ea22")
    (sq,) = load_source_queries(tmp_path)
    assert sq.rel_path == "real-estate/broker/mortgage.chicago.ea22"


def test_finds_all_queries_sorted(tmp_path):
    write_query(tmp_path, "real-estate/broker/mortgage.chicago.ea22")
    write_query(tmp_path, "finance/stocks/tech.baf3")
    queries = load_source_queries(tmp_path)
    assert [q.rel_path for q in queries] == [
        "finance/stocks/tech.baf3",
        "real-estate/broker/mortgage.chicago.ea22",
    ]


def test_missing_root_raises(tmp_path):
    with pytest.raises(SourceError):
        load_source_queries(tmp_path / "nope")


def test_malformed_query_raises(tmp_path):
    write_query(tmp_path, "x/y/z", text="query: hi\n")  # no metadata.id
    with pytest.raises(SourceError):
        load_source_queries(tmp_path)
