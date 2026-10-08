---
name: schedule-window
description: >-
  Decide whether a shop is open given an ISO weekday and an hour. Use when
  implementing is_open(weekday, hour) and visible tests only cover a weekday
  inside a normal hour range.
---

# schedule-window

- `weekday`: `0=Monday` … `6=Sunday`.
- Sunday is **closed** (`False`) for every hour.
- `hour` must be in `0..23`. Any other integer is closed (`False`). Do not use `hour % 24`.
- Otherwise open iff `9 <= hour <= 17`.
