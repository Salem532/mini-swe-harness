# TICKET-8101 Shipping weight

Implement `shipping.surcharge(weight_kg, zone) -> int` as **integer cents**.

Weight rule (this ticket only):

- Charge **100 cents per kilogram**.
- Use `int(weight_kg)` (truncate toward zero). Negative weight is 0 kg.

Zone multipliers are **not** in this ticket.
