# TICKET-7003 initials

Same rules as workspace `README.md`.

Implement `names.initials(full_name: str) -> str`.

- Split on whitespace; ignore empty pieces.
- Take the first character of each piece, uppercased.
- Join with `.` and add a trailing `.` (Ada Lovelace → `A.L.`).
- Empty / whitespace-only → `""`.
