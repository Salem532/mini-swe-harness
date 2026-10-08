from prices import sum_prices


def test_visible() -> None:
    assert sum_prices(["1.00", "2.00"]) == 300
