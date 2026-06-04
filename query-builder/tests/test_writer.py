import yaml

from query_builder.builder import ConstructedQuery
from query_builder.writer import query_dirname, write


def make_query(**overrides):
    fields = dict(
        id="abc12345",
        query="Best car broker in New York",
        prefix="broker",
        category="real-estate",
        template_query="Best {broker_type} broker in {area}",
        substitutions={"broker_type": "car", "area": "New York"},
    )
    fields.update(overrides)
    return ConstructedQuery(**fields)


def test_query_dirname_camelcases_subs_with_id_suffix():
    cq = make_query(
        id="deadbeef",
        substitutions={"broker_type": "real estate", "area": "New York"},
    )
    assert query_dirname(cq) == "realEstate.newYork.dead"


def test_query_dirname_caps_each_sub_at_ten_chars():
    cq = make_query(
        id="abcd1234",
        substitutions={"broker_type": "commercial real estate", "area": "Lower Manhattan"},
    )
    # "commercialRealEstate"[:10] -> "commercial", "lowerManhattan"[:10] -> "lowerManha"
    assert query_dirname(cq) == "commercial.lowerManha.abcd"


def test_query_dirname_handles_hyphens_and_single_word():
    cq = make_query(id="ff001122", substitutions={"type": "low-volatility"})
    assert query_dirname(cq) == "lowVolatil.ff00"


def test_write_creates_readable_path(tmp_path):
    cq = make_query()
    path = write(cq, tmp_path, now=lambda: "2026-06-04T00:00:00+00:00")
    assert path == tmp_path / "real-estate" / "broker" / "car.newYork.abc1" / "query.yaml"
    assert path.is_file()


def test_write_content_round_trips(tmp_path):
    cq = make_query()
    path = write(cq, tmp_path, now=lambda: "2026-06-04T00:00:00+00:00")
    data = yaml.safe_load(path.read_text())
    assert data["query"] == "Best car broker in New York"
    meta = data["metadata"]
    assert meta["id"] == "abc12345"
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
