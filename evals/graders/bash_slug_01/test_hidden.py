from textutil.slug import slugify


def test_hidden() -> None:
    assert slugify("ABC 123") == "abc-123"
    assert slugify("go--fast") == "go-fast"
    assert slugify("  hi  ") == "hi"
