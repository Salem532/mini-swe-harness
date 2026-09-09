---
name: repo-qa
description: Check repository invariants before declaring done — encoding, empty inputs, public API shape, rounding, and format edge cases that smoke tests often miss. Use when finishing a bugfix, when a parser/config/file-format task might have hidden edge cases, or when you need a verification matrix.
---

# repo-qa

Visible tests in this harness are incomplete on purpose. Before submitting, walk the verification matrix in `references/verification-matrix.md`.

## Procedure

1. Identify the public function the prompt names.
2. Write a tiny driver (print-based or a throwaway script under `/tmp`) that hits edge cases from the matrix. Do not add files under `tests/` (read-only).
3. Encoding: if the code reads text files, try UTF-8 with a BOM (`utf-8-sig`) and an empty file.
4. Config/JSON: empty or whitespace-only input should yield a documented default, not a crash.
5. Numeric money/tax: use integer cents or `Decimal`; do not leave binary float in the public API if the matrix says otherwise.
6. Submit only after the matrix rows you can exercise locally have passed.

Load the matrix with:

```bash
cat /workspace/.agents/skills/repo-qa/references/verification-matrix.md
```
