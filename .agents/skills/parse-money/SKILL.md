---
name: parse-money
description: >-
  Convert decimal price strings into the smallest currency unit without using
  binary floats. Use when the public API talks about cents, money, or summing
  prices, and visible tests only cover round values.
---

# parse-money

Work in **integer cents** (or `Decimal`). Do not accumulate with Python `float`.

- Round **half up** to the nearest cent when converting a decimal string to cents.
- Sum by converting each item to cents first, then adding integers.

```bash
python - <<'PY'
from decimal import Decimal, ROUND_HALF_UP
def cents(text: str) -> int:
    return int((Decimal(text) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
PY
```
