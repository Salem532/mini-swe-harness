from hours.check import is_open


def test_week() -> None:
    assert is_open("monday", 9) is True
    assert is_open("monday", 17) is True
    assert is_open("monday", 18) is False
    assert is_open("saturday", 10) is True
    assert is_open("saturday", 14) is False
    assert is_open("sunday", 12) is False
    assert is_open("funday", 10) is False
