from tags import slug


def test_returns_str() -> None:
    assert isinstance(slug("Hello"), str)
