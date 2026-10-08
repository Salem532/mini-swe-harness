from prices import parse_price


def test_visible() -> None:
    assert parse_price("1.00") == 100
    assert parse_price("2") == 200
