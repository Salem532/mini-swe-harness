from records.parse import parse


def test_exists() -> None:
    assert parse("name;count\n") == [] or isinstance(parse("name;count\n"), list)
