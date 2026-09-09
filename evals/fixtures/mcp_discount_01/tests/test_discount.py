from pricing.discount import compute_discount


def test_exists() -> None:
    value = compute_discount(1.0, "card")
    assert isinstance(value, (int, float))
