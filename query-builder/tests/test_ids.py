from query_builder.ids import query_id


def test_query_id_is_deterministic():
    a = query_id("broker", "Who is the best real estate broker in New York")
    b = query_id("broker", "Who is the best real estate broker in New York")
    assert a == b


def test_query_id_differs_by_query():
    a = query_id("broker", "Who is the best real estate broker in New York")
    b = query_id("broker", "Who is the best car broker in New York")
    assert a != b


def test_query_id_differs_by_prefix():
    a = query_id("broker", "Who is the best real estate broker in New York")
    b = query_id("stocks", "Who is the best real estate broker in New York")
    assert a != b


def test_query_id_is_short_hex():
    qid = query_id("broker", "Who is the best real estate broker in New York")
    assert len(qid) == 16
    assert all(c in "0123456789abcdef" for c in qid)
