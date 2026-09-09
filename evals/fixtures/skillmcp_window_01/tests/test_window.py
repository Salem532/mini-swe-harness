from window.check import contains


def test_exists() -> None:
    assert isinstance(contains(0, 10, 5), bool)
