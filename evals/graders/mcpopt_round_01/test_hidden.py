from decimal import ROUND_HALF_UP, Decimal

from money.cents import round_cents


def _expected(amount: float) -> float:
    quant = Decimal("0.01")
    value = Decimal(str(amount)).quantize(quant, rounding=ROUND_HALF_UP)
    return float(value)


def test_half_up() -> None:
    assert round_cents(1.005) == _expected(1.005)
    assert round_cents(-1.005) == _expected(-1.005)
    assert round_cents(2.0) == 2.0
    assert round_cents(0.014) == 0.01
