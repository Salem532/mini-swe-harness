from jsoncfg.loader import load_config


def test_empty_string() -> None:
    assert load_config("") == {}


def test_whitespace() -> None:
    assert load_config("  \n") == {}
