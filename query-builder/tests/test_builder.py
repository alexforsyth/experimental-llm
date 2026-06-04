from query_builder.builder import build
from query_builder.ids import query_id
from query_builder.template import Template


def make_template(tmp_path, text, category="real-estate", name="broker.yaml"):
    d = tmp_path / category
    d.mkdir(parents=True, exist_ok=True)
    path = d / name
    path.write_text(text)
    return Template.load(path)


def test_build_produces_cartesian_product(tmp_path):
    tmpl = make_template(
        tmp_path,
        'Query: "Who is the best {broker_type} broker in {area}"\n'
        "Subs:\n"
        '  broker_type: ["real estate", "car"]\n'
        '  area: ["New York", "Brooklyn", "Queens"]\n',
    )
    queries = build(tmpl)
    assert len(queries) == 2 * 3


def test_build_resolves_query_text(tmp_path):
    tmpl = make_template(
        tmp_path,
        'Query: "Best {broker_type} broker in {area}"\n'
        "Subs:\n"
        '  broker_type: ["car"]\n'
        '  area: ["New York"]\n',
    )
    (cq,) = build(tmpl)
    assert cq.query == "Best car broker in New York"
    assert cq.substitutions == {"broker_type": "car", "area": "New York"}


def test_build_sets_metadata_fields(tmp_path):
    tmpl = make_template(
        tmp_path,
        'Query: "Best {area} broker"\nSubs:\n  area: ["NY"]\n',
    )
    (cq,) = build(tmpl)
    assert cq.prefix == "broker"
    assert cq.category == "real-estate"
    assert cq.template_query == "Best {area} broker"
    assert cq.id == query_id("broker", "Best NY broker")


def test_build_ids_are_unique(tmp_path):
    tmpl = make_template(
        tmp_path,
        'Query: "Best {broker_type} broker in {area}"\n'
        "Subs:\n"
        '  broker_type: ["real estate", "car", "mortgage"]\n'
        '  area: ["New York", "Brooklyn"]\n',
    )
    ids = [cq.id for cq in build(tmpl)]
    assert len(ids) == len(set(ids))


def test_build_is_deterministic(tmp_path):
    text = (
        'Query: "Best {broker_type} broker in {area}"\n'
        "Subs:\n"
        '  broker_type: ["real estate", "car"]\n'
        '  area: ["New York", "Brooklyn"]\n'
    )
    a = [cq.query for cq in build(make_template(tmp_path / "a", text))]
    b = [cq.query for cq in build(make_template(tmp_path / "b", text))]
    assert a == b
