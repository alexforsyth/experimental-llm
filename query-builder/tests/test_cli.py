from query_builder.cli import main


def write_template(root, category, name, text):
    d = root / category
    d.mkdir(parents=True, exist_ok=True)
    path = d / name
    path.write_text(text)
    return path


BROKER = (
    'Query: "Who is the best {broker_type} broker in {area}"\n'
    "Subs:\n"
    '  broker_type: ["real estate", "car"]\n'
    '  area: ["New York", "Brooklyn", "Queens"]\n'
)


def test_build_single_file_writes_queries(tmp_path, capsys):
    tmpl = write_template(tmp_path / "templates", "real-estate", "broker.yaml", BROKER)
    out = tmp_path / "queries"

    code = main(["build", str(tmpl), "--out", str(out)])

    assert code == 0
    written = list(out.rglob("query.yaml"))
    assert len(written) == 6
    assert all(p.parent.parent.name == "broker" for p in written)
    assert "6" in capsys.readouterr().out


def test_build_directory_builds_all_templates(tmp_path):
    write_template(tmp_path / "templates", "real-estate", "broker.yaml", BROKER)
    write_template(
        tmp_path / "templates",
        "finance",
        "stocks.yaml",
        'Query: "Best {type} stock?"\nSubs:\n  type: ["tech", "value"]\n',
    )
    out = tmp_path / "queries"

    code = main(["build", str(tmp_path / "templates"), "--out", str(out)])

    assert code == 0
    assert len(list((out / "broker").rglob("query.yaml"))) == 6
    assert len(list((out / "stocks").rglob("query.yaml"))) == 2


def test_dry_run_writes_nothing(tmp_path, capsys):
    tmpl = write_template(tmp_path / "templates", "real-estate", "broker.yaml", BROKER)
    out = tmp_path / "queries"

    code = main(["build", str(tmpl), "--out", str(out), "--dry-run"])

    assert code == 0
    assert not out.exists()
    assert "6" in capsys.readouterr().out


def test_missing_path_returns_error(tmp_path, capsys):
    code = main(["build", str(tmp_path / "nope.yaml")])
    assert code != 0
    assert "nope.yaml" in capsys.readouterr().err


def test_invalid_template_returns_error(tmp_path, capsys):
    tmpl = write_template(
        tmp_path / "templates",
        "x",
        "bad.yaml",
        'Query: "{a} {b}"\nSubs:\n  a: ["1"]\n',
    )
    code = main(["build", str(tmpl), "--out", str(tmp_path / "queries")])
    assert code != 0
    assert "b" in capsys.readouterr().err
