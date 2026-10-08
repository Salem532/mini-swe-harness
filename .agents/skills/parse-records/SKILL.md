---
name: parse-records
description: >-
  Parse line-oriented records that may include comments or a delimiter other
  than comma. Use when splitting payloads into lines or fields and smoke tests
  only show the simple case.
---

# parse-records

- After splitting on newlines, drop lines whose first non-space character is `#`.
- Field delimiter is the pipe character, not comma. Split rows on `|`.
