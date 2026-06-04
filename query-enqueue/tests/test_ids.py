from query_enqueue.ids import enqueue_id


def test_enqueue_id_is_stable():
    a = enqueue_id("ea227897d0dc8c32", "anthropic", "claude-opus-4-8")
    b = enqueue_id("ea227897d0dc8c32", "anthropic", "claude-opus-4-8")
    assert a == b


def test_enqueue_id_differs_by_model():
    opus = enqueue_id("ea227897d0dc8c32", "anthropic", "claude-opus-4-8")
    sonnet = enqueue_id("ea227897d0dc8c32", "anthropic", "claude-sonnet-4-6")
    assert opus != sonnet


def test_enqueue_id_differs_by_provider():
    direct = enqueue_id("ea227897d0dc8c32", "anthropic", "claude-opus-4-8")
    bedrock = enqueue_id("ea227897d0dc8c32", "bedrock", "claude-opus-4-8")
    assert direct != bedrock


def test_enqueue_id_differs_by_query():
    a = enqueue_id("ea227897d0dc8c32", "anthropic", "claude-opus-4-8")
    b = enqueue_id("17fbdeadbeef0000", "anthropic", "claude-opus-4-8")
    assert a != b


def test_enqueue_id_is_short_hex():
    value = enqueue_id("ea227897d0dc8c32", "anthropic", "claude-opus-4-8")
    assert len(value) == 16
    assert all(c in "0123456789abcdef" for c in value)
