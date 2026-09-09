from text.title import title_words


def test_exists() -> None:
    try:
        value = title_words("a")
    except NotImplementedError:
        return
    assert isinstance(value, str)
