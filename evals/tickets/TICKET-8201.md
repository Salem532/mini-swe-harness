# TICKET-8201 Role names

Implement `roles.normalize(name: str) -> str`.

- Strip leading/trailing whitespace.
- Lowercase.
- If the result is empty, return `"guest"`.
- If the result is `"admin"`, return `"administrator"`.
- Otherwise return the stripped lowercase string.

Do not uppercase. Do not keep inner padding.
