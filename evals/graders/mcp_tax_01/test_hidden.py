from decimal import Decimal, ROUND_HALF_UP

from tax.sales import sales_tax


def _ref(amount: str) -> str:
    value = Decimal(amount or "0") * Decimal("0.08875")
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def test_rate_and_rounding() -> None:
    assert sales_tax("1.00") == _ref("1.00")
    assert sales_tax("0") == "0.00"
    assert sales_tax("19.99") == _ref("19.99")
