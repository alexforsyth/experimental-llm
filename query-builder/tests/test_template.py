import pytest

from query_builder.template import Template, TemplateError


def write_template(tmp_path, category, name, text):
    d = tmp_path / category
    d.mkdir(parents=True, exist_ok=True)
    path = d / name
    path.write_text(text)
    return path


def test_load_parses_query_and_subs(tmp_path):
    path = write_template(
        tmp_path,
        "real-estate",
        "broker.yaml",
        'Query: "Who is the best {broker_type} broker in {area}"\n'
        "Subs:\n"
        '  broker_type: ["real estate", "car"]\n'
        '  area: ["New York", "Brooklyn"]\n',
    )
    tmpl = Template.load(path)
    assert tmpl.query == "Who is the best {broker_type} broker in {area}"
    assert tmpl.subs == {
        "broker_type": ["real estate", "car"],
        "area": ["New York", "Brooklyn"],
    }


def test_load_derives_prefix_and_category(tmp_path):
    path = write_template(
        tmp_path,
        "real-estate",
        "broker.yaml",
        'Query: "Best {area} broker"\nSubs:\n  area: ["NY"]\n',
    )
    tmpl = Template.load(path)
    assert tmpl.prefix == "broker"
    assert tmpl.category == "real-estate"


def test_placeholders_property(tmp_path):
    path = write_template(
        tmp_path,
        "x",
        "t.yaml",
        'Query: "{a} and {b}"\nSubs:\n  a: ["1"]\n  b: ["2"]\n',
    )
    assert Template.load(path).placeholders == {"a", "b"}


def test_missing_sub_for_placeholder_raises(tmp_path):
    path = write_template(
        tmp_path,
        "x",
        "t.yaml",
        'Query: "{a} and {b}"\nSubs:\n  a: ["1"]\n',
    )
    with pytest.raises(TemplateError, match="b"):
        Template.load(path)


def test_unused_sub_raises(tmp_path):
    path = write_template(
        tmp_path,
        "x",
        "t.yaml",
        'Query: "{a}"\nSubs:\n  a: ["1"]\n  b: ["2"]\n',
    )
    with pytest.raises(TemplateError, match="b"):
        Template.load(path)


def test_empty_sub_list_raises(tmp_path):
    path = write_template(
        tmp_path,
        "x",
        "t.yaml",
        'Query: "{a}"\nSubs:\n  a: []\n',
    )
    with pytest.raises(TemplateError, match="empty"):
        Template.load(path)


def test_missing_query_key_raises(tmp_path):
    path = write_template(tmp_path, "x", "t.yaml", 'Subs:\n  a: ["1"]\n')
    with pytest.raises(TemplateError, match="Query"):
        Template.load(path)


def test_missing_file_raises(tmp_path):
    with pytest.raises(TemplateError, match="not found"):
        Template.load(tmp_path / "nope.yaml")
