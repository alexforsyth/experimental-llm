import yaml

from query_enqueue.config import ModelTarget
from query_enqueue.enqueuer import EnqueuedQuery
from query_enqueue.writer import enqueued_path, model_slug, write


def make_enqueued(model=None, **overrides):
    fields = dict(
        enqueue_id="abcd1234abcd1234",
        model=model or ModelTarget(name="claude-opus-4-8", provider="anthropic"),
        query_id="ea227897d0dc8c32",
        query="Best mortgage broker in Chicago",
        prefix="broker",
        category="real-estate",
        source="real-estate/broker/mortgage.chicago.ea22",
    )
    fields.update(overrides)
    return EnqueuedQuery(**fields)


def test_model_slug_keeps_safe_chars():
    assert model_slug("claude-opus-4-8") == "claude-opus-4-8"


def test_model_slug_replaces_unsafe_chars():
    assert model_slug("llama3.1:8b") == "llama3.1-8b"


def test_enqueued_path_leaf_is_provider_dot_model(tmp_path):
    enq = make_enqueued()
    path = enqueued_path(enq, tmp_path)
    assert path == (
        tmp_path
        / "real-estate/broker/mortgage.chicago.ea22"
        / "anthropic.claude-opus-4-8"
        / "query.yaml"
    )


def test_write_serializes_target(tmp_path):
    model = ModelTarget(
        name="claude-opus-4-8",
        provider="anthropic",
        options={"max_tokens": 1024},
    )
    path = write(make_enqueued(model=model), tmp_path, now=lambda: "2026-06-04T00:00:00+00:00")
    data = yaml.safe_load(path.read_text())
    assert data["query"] == "Best mortgage broker in Chicago"
    assert data["target"] == {
        "provider": "anthropic",
        "name": "claude-opus-4-8",
        "max_tokens": 1024,
    }
    meta = data["metadata"]
    assert meta["enqueue_id"] == "abcd1234abcd1234"
    assert meta["query_id"] == "ea227897d0dc8c32"
    assert meta["prefix"] == "broker"
    assert meta["category"] == "real-estate"
    assert meta["source"] == "real-estate/broker/mortgage.chicago.ea22/query.yaml"
    assert meta["enqueued_at"] == "2026-06-04T00:00:00+00:00"


def test_target_has_no_connection_details(tmp_path):
    path = write(make_enqueued(), tmp_path)
    data = yaml.safe_load(path.read_text())
    assert set(data["target"]) == {"provider", "name"}
    assert "base_url" not in data["target"]
    assert "auth" not in data["target"]


def test_same_model_two_providers_do_not_collide(tmp_path):
    direct = write(make_enqueued(model=ModelTarget(name="claude-opus-4-8", provider="anthropic")), tmp_path)
    bedrock = write(make_enqueued(model=ModelTarget(name="claude-opus-4-8", provider="bedrock")), tmp_path)
    assert direct != bedrock
    assert direct.is_file() and bedrock.is_file()


def test_rerun_preserves_enqueued_at(tmp_path):
    write(make_enqueued(), tmp_path, now=lambda: "2026-01-01T00:00:00+00:00")
    path = write(make_enqueued(), tmp_path, now=lambda: "2099-12-31T23:59:59+00:00")
    data = yaml.safe_load(path.read_text())
    assert data["metadata"]["enqueued_at"] == "2026-01-01T00:00:00+00:00"
