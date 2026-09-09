# TICKET-2210 Sales tax

Implement `tax.sales_tax(amount: str) -> str`.

- Input and output are decimal strings, not floats.
- Tax rate is **8.875%**.
- Round **half up** to two decimal places (cents).
- Empty or zero amount → `"0.00"`.

Example: `sales_tax("1.00")` → `"0.09"` because 0.08875 rounds half up to 0.09.
