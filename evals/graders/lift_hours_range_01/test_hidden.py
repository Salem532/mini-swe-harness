from shop import is_open


def test_hidden() -> None:
    assert is_open(0, 33) is False
