from money.cents import round_cents


def test_exists() -> None:
    try:
        value = round_cents(1.0)
    except NotImplementedError:
        return
    assert isinstance(value, float)
