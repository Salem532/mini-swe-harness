from jsoncfg.loader import load_config


def test_object() -> None:
    assert load_config('{"a": 1}') == {"a": 1}
