from records.parse import parse

SAMPLE = "\ufeffname;count\n# ignore\nalice;3\n\nbob;4\n"


def test_format() -> None:
    rows = parse(SAMPLE)
    assert rows == [{"name": "alice", "count": 3}, {"name": "bob", "count": 4}]
