from window.check import contains


def test_half_open() -> None:
    assert contains(0, 10, 0) is True
    assert contains(0, 10, 10) is False
    assert contains(5, 4, 5) is False
    assert contains(2, 8, 7) is True
