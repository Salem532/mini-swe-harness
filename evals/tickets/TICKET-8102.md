# TICKET-8102 Shipping zone

Zone multipliers for `shipping.surcharge` (this ticket only):

- `"A"` → 1
- `"B"` → 2
- `"C"` → 3
- any other zone → 0 (no surcharge)

Combine with the weight ticket: `cents = kg * 100 * multiplier`.
