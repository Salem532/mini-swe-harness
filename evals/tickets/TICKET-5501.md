# TICKET-5501 Record file format

Implement `records.parse(text: str) -> list[dict]`.

- Delimiter is **semicolon** `;`, not comma.
- Lines whose first non-space character is `#` are comments; skip them.
- Blank lines: skip.
- Header row is required: `name;count`
- Each data row becomes `{"name": str, "count": int}`.
- UTF-8 BOM on the first line must be ignored.
