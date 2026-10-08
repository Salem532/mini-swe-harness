from shipping import surcharge


def test_returns_int() -> None:
    assert isinstance(surcharge(1, "A"), int)
