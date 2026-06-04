from query_enqueue.config import EnqueueConfig, ModelTarget
from query_enqueue.enqueuer import EnqueuedQuery, enqueue, is_ignored
from query_enqueue.ids import enqueue_id
from query_enqueue.source import SourceQuery


def make_source(rel_path, id="ea227897d0dc8c32", query="Best mortgage broker in Chicago"):
    return SourceQuery(
        id=id,
        query=query,
        prefix="broker",
        category="real-estate",
        rel_path=rel_path,
        path=None,
    )


def model(name, provider="anthropic", **options):
    return ModelTarget(name=name, provider=provider, options=options)


def cfg(models, ignore=None):
    return EnqueueConfig(models=models, ignore=ignore or [])


def test_fans_each_query_out_to_every_model():
    src = [make_source("real-estate/broker/mortgage.chicago.ea22")]
    out = enqueue(src, cfg([model("claude-opus-4-8"), model("claude-sonnet-4-6")]))
    assert len(out) == 2
    assert {e.model.name for e in out} == {"claude-opus-4-8", "claude-sonnet-4-6"}


def test_carries_full_model_target():
    opus = model("claude-opus-4-8", max_tokens=8)
    src = [make_source("real-estate/broker/mortgage.chicago.ea22")]
    (e,) = enqueue(src, cfg([opus]))
    assert e.model is opus


def test_carries_query_back_reference():
    src = [make_source("real-estate/broker/mortgage.chicago.ea22")]
    (e,) = enqueue(src, cfg([model("claude-opus-4-8")]))
    assert e.query_id == "ea227897d0dc8c32"
    assert e.query == "Best mortgage broker in Chicago"
    assert e.prefix == "broker"
    assert e.category == "real-estate"
    assert e.source == "real-estate/broker/mortgage.chicago.ea22"
    assert e.enqueue_id == enqueue_id("ea227897d0dc8c32", "anthropic", "claude-opus-4-8")


def test_enqueue_id_factors_in_provider():
    src = [make_source("real-estate/broker/mortgage.chicago.ea22")]
    direct = enqueue(src, cfg([model("claude-opus-4-8", provider="anthropic")]))[0]
    bedrock = enqueue(src, cfg([model("claude-opus-4-8", provider="bedrock")]))[0]
    assert direct.enqueue_id != bedrock.enqueue_id


def test_ignore_glob_skips_matching_queries():
    src = [
        make_source("finance/stocks/tech.baf3", id="aaaa"),
        make_source("real-estate/broker/mortgage.chicago.ea22", id="bbbb"),
    ]
    out = enqueue(src, cfg([model("claude-opus-4-8")], ignore=["finance/**"]))
    assert [e.source for e in out] == ["real-estate/broker/mortgage.chicago.ea22"]


def test_ignore_applies_before_fanout():
    src = [make_source("finance/stocks/tech.baf3")]
    out = enqueue(src, cfg([model("m1"), model("m2")], ignore=["finance/stocks/tech.baf3"]))
    assert out == []


def test_output_is_deterministic():
    src = [
        make_source("real-estate/broker/a.1111", id="1111"),
        make_source("real-estate/broker/b.2222", id="2222"),
    ]
    out = enqueue(src, cfg([model("m1"), model("m2")]))
    assert [(e.source, e.model.name) for e in out] == [
        ("real-estate/broker/a.1111", "m1"),
        ("real-estate/broker/a.1111", "m2"),
        ("real-estate/broker/b.2222", "m1"),
        ("real-estate/broker/b.2222", "m2"),
    ]


def test_is_ignored_matches_directory_glob():
    assert is_ignored("real-estate/broker/car.chicago.94a6", ["real-estate/broker/car.*"])
    assert not is_ignored("real-estate/broker/mortgage.chicago.ea22", ["real-estate/broker/car.*"])


def test_is_ignored_with_no_patterns():
    assert not is_ignored("anything/at/all", [])
