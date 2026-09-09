# TICKET-6602 Booking window

Implement `window.contains(start: int, end: int, ts: int) -> bool`.

- The window is **half-open**: start inclusive, end exclusive.
- If `end < start` the window is invalid → always False.
- `ts == end` is **outside**.
- `ts == start` is inside when start < end.
