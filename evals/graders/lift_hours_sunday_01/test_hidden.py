from shop import is_open


def test_hidden() -> None:
    assert is_open(6, 10) is False
