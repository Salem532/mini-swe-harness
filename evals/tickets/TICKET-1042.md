# TICKET-1042 Discount rules

Implement `pricing.compute_discount(amount: float, method: str) -> float`.

Rules:

- `method == "gift_card"`: always `0.0` (no discount).
- Otherwise:
  - amount > 500: 15% of amount
  - amount > 100: 10% of amount
  - else: 0.0
- Return a float. Do not round.

Example: `compute_discount(200, "card") == 20.0`.
