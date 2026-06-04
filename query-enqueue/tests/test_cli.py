import yaml

from query_enqueue.cli import main

QUERY_YAML = (
    "query: Best mortgage broker in Chicago\n"
    "metadata:\n"
    "  id: ea227897d0dc8c32\n"
    "  prefix: broker\n"
    "  category: real-estate\n"
)

PROVIDERS = (
    "providers:\n"
    "  anthropic:\n"
    "    type: anthropic\n"
    "    base_url: https://api.anthropic.com\n"
    "    auth: {type: env, var: ANTHROPIC_API_KEY}\n"
)

CONFIG = (
    "models:\n"
    "  - name: claude-opus-4-8\n"
    "    provider: anthropic\n"
    "  - name: claude-sonnet-4-6\n"
    "    provider: anthropic\n"
)


def write_query(root, rel, id="ea227897d0dc8c32"):
    text = QUERY_YAML.replace("ea227897d0dc8c32", id)
    path = root / rel / "query.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def write_file(root, name, text):
    path = root / name
    path.write_text(text)
    return path


def base(tmp_path, config_text=CONFIG, providers_text=PROVIDERS):
    qdir = tmp_path / "queries"
    write_query(qdir, "real-estate/broker/mortgage.chicago.ea22")
    cfg = write_file(tmp_path, "enqueue.yaml", config_text)
    prov = write_file(tmp_path, "providers.yaml", providers_text)
    out = tmp_path / "enqueued_queries"
    return qdir, cfg, prov, out


def run(qdir, cfg, prov, out, *extra):
    return main(
        ["enqueue", str(qdir), "--config", str(cfg), "--providers", str(prov), "--out", str(out), *extra]
    )


def test_enqueue_fans_out_to_each_model(tmp_path, capsys):
    qdir, cfg, prov, out = base(tmp_path)
    assert run(qdir, cfg, prov, out) == 0
    assert len(list(out.rglob("query.yaml"))) == 2
    assert "2" in capsys.readouterr().out


def test_enqueue_respects_ignore(tmp_path):
    qdir, cfg, prov, out = base(tmp_path, config_text=CONFIG + 'ignore:\n  - "finance/**"\n')
    write_query(qdir, "finance/stocks/tech.baf3", id="aaaa")
    assert run(qdir, cfg, prov, out) == 0
    assert not (out / "finance").exists()
    assert len(list((out / "real-estate").rglob("query.yaml"))) == 2


def test_dry_run_writes_nothing(tmp_path, capsys):
    qdir, cfg, prov, out = base(tmp_path)
    assert run(qdir, cfg, prov, out, "--dry-run") == 0
    assert not out.exists()
    assert "2" in capsys.readouterr().out


def test_written_file_carries_provider_reference(tmp_path):
    config = (
        "models:\n"
        "  - name: claude-opus-4-8\n"
        "    provider: anthropic\n"
        "    max_tokens: 1024\n"
    )
    qdir, cfg, prov, out = base(tmp_path, config_text=config)
    run(qdir, cfg, prov, out)
    (path,) = list(out.rglob("query.yaml"))
    data = yaml.safe_load(path.read_text())
    assert data["target"] == {
        "provider": "anthropic",
        "name": "claude-opus-4-8",
        "max_tokens": 1024,
    }


def test_unknown_provider_errors(tmp_path, capsys):
    config = "models:\n  - name: m\n    provider: nope\n"
    qdir, cfg, prov, out = base(tmp_path, config_text=config)
    assert run(qdir, cfg, prov, out) != 0
    assert "nope" in capsys.readouterr().err


def test_missing_providers_file_errors(tmp_path, capsys):
    qdir, cfg, _, out = base(tmp_path)
    assert run(qdir, cfg, tmp_path / "nope.yaml", out) != 0
    assert capsys.readouterr().err


def test_missing_queries_dir_errors(tmp_path, capsys):
    _, cfg, prov, out = base(tmp_path)
    assert run(tmp_path / "nope", cfg, prov, out) != 0
    assert capsys.readouterr().err


def test_bad_config_errors(tmp_path, capsys):
    qdir, cfg, prov, out = base(tmp_path, config_text="models: []\n")
    assert run(qdir, cfg, prov, out) != 0
    assert capsys.readouterr().err
