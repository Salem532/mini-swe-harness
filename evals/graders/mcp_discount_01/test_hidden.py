from pricing.discount import compute_discount


def test_rules() -> None:
    assert compute_discount(50, "card") == 0.0
    assert compute_discount(200, "card") == 20.0
    assert compute_discount(501, "card") == 501 * 0.15
    assert compute_discount(999, "gift_card") == 0.0
