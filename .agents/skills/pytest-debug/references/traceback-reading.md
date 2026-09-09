# Reading pytest tracebacks

- The last `E   AssertionError` line is the claim that failed; the `>` line is the source.
- `short test summary info` lists node ids. Copy those, do not re-run the whole module.
- A test named `test_integration_*` or marked `slow` is often unrelated to the bug. Skip it while iterating.
- Fixtures that fail in `setup` show as `ERROR` not `FAILED`. Fix setup data, not the assertion.
- Never edit tests in this harness; they are mounted read-only. Change `src/` only.
