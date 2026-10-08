from prices import parse_price


def test_hidden() -> None:
    assert parse_price("1.005") == 101
