import yaml

from query_builder.builder import ConstructedQuery
from query_builder.writer import write


def make_query():
    return ConstructedQuery(
        id="abc123",
        query="Best car broker in New York",
        prefix="broker",
        category="real-estate",
        template_query="Best {broker_type} broker in {area}",
        substitutions={"broker_type": "car", "area": "New York"},
    )


def test_write_creates_expected_path(tmp_path):
    cq = make_query()
    path = write(cq, tmp_path, now=lambda: "2026-06-04T00:00:00+00:00")
    assert path == tmp_path / "broker" / "abc123" / "query.yaml"
    assert path.is_file()


def test_write_content_round_trips(tmp_path):
    cq = make_query()
    path = write(cq, tmp_path, now=lambda: "2026-06-04T00:00:00+00:00")
    data = yaml.safe_load(path.read_text())
    assert data["query"] == "Best car broker in New York"
    meta = data["metadata"]
    assert meta["id"] == "abc123"
    assert meta["prefix"] == "broker"
    assert meta["category"] == "real-estate"
    assert meta["template_query"] == "Best {broker_type} broker in {area}"
    assert meta["substitutions"] == {"broker_type": "car", "area": "New York"}
    assert meta["created_at"] == "2026-06-04T00:00:00+00:00"


def test_rerun_preserves_created_at(tmp_path):
    cq = make_query()
    write(cq, tmp_path, now=lambda: "2026-01-01T00:00:00+00:00")
    path = write(cq, tmp_path, now=lambda: "2099-12-31T23:59:59+00:00")
    data = yaml.safe_load(path.read_text())
    assert data["metadata"]["created_at"] == "2026-01-01T00:00:00+00:00"
