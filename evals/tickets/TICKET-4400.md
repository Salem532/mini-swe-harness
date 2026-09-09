# TICKET-4400 Invoice total

Implement `invoice.total(lines: list[dict]) -> str`.

Each line: `{"qty": int, "unit_price": str, "taxable": bool}`.

- Line subtotal = qty * unit_price (decimal strings internally).
- qty <= 0 or missing: skip the line (contribute 0).
- Sum subtotals, then add tax **8.250%** only on lines with `taxable=True`.
- Round the **final** total half-up to two decimals. Return a string like `"12.34"`.
