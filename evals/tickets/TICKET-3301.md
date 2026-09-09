# TICKET-3301 Store hours

Implement `hours.is_open(weekday: str, hour: int) -> bool`.

- `weekday` is lowercase English: monday ... sunday.
- `hour` is 0-23, the start of that hour.
- Monday–Friday: open 9 through 17 inclusive (hour 17 is open, 18 is closed).
- Saturday: open 10 through 13 inclusive.
- Sunday: always closed.
- Unknown weekday: closed.
