# Verification matrix

Run these mentally or with a `/tmp` driver against the public API. Visible tests will not cover all rows.

| Area | Input | Expected |
|------|-------|----------|
| CSV / text | file starts with UTF-8 BOM (`\ufeff`) | BOM is stripped; first header is a normal name |
| CSV / text | empty file | empty list / empty dict, not an exception |
| JSON config | `""` or whitespace | `{}` |
| JSON config | `{"a": 1}` | dict with key `a` |
| Money | values that look like `1.005` | round **half up** to cents if the spec talks about money |
| Records | lines starting with `#` | treated as comments when a ticket/format says so |
| Records | delimiter other than comma | honor the ticket; do not assume CSV commas |
| Hours / windows | Sunday or out-of-range | closed / reject, never wrap silently |
| Public API | function exists | keep the advertised name and signature |

If a ticket is named in the prompt, the ticket wins over this matrix when they conflict.
