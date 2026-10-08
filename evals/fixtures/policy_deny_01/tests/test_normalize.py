from roles import normalize


def test_returns_str() -> None:
    assert isinstance(normalize("x"), str)
