from hours.check import is_open


def test_exists() -> None:
    assert isinstance(is_open("monday", 10), bool)
