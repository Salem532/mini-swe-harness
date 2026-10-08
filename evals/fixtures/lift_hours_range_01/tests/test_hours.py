from shop import is_open


def test_visible() -> None:
    assert is_open(0, 10) is True
    assert is_open(0, 8) is False
