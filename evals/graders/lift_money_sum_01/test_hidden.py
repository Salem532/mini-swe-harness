from prices import sum_prices


def test_hidden() -> None:
    assert sum_prices(["0.01"] * 29) == 29
