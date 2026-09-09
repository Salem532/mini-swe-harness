from tax.sales import sales_tax


def test_exists() -> None:
    assert isinstance(sales_tax("1.00"), str)
