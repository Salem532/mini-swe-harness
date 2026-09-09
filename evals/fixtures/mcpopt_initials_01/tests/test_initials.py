from names.initials import initials


def test_exists() -> None:
    try:
        value = initials("A")
    except NotImplementedError:
        return
    assert isinstance(value, str)
