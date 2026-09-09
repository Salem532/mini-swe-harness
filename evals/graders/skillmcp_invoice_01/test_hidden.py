from decimal import Decimal, ROUND_HALF_UP

from invoice.total import total


def test_zero_qty_and_tax() -> None:
    lines = [
        {"qty": 2, "unit_price": "10.00", "taxable": True},
        {"qty": 0, "unit_price": "99.00", "taxable": True},
        {"qty": 1, "unit_price": "5.00", "taxable": False},
    ]
    sub_taxable = Decimal("20.00")
    taxed = sub_taxable + sub_taxable * Decimal("0.0825")
    expected = (taxed + Decimal("5.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    assert total(lines) == str(expected)
