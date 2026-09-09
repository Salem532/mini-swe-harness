from text.title import title_words


def test_rules() -> None:
    assert title_words("hello world") == "Hello World"
    assert title_words("  ADA   lovelace ") == "Ada Lovelace"
    assert title_words("") == ""
    assert title_words("\t") == ""
    assert title_words("é") == "É"
