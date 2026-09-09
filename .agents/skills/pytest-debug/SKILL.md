---
name: pytest-debug
description: Diagnose failing pytest runs by isolating the failing node, reading the traceback, and re-running one test. Use when pytest fails, an assertion error appears, a suite is slow, or you need to avoid rerunning the whole file after a single failure.
---

# pytest-debug

Keep the loop small. A full-suite rerun is the usual way this environment hits a command timeout.

## Procedure

1. If you have not run tests yet, start with a focused path (`pytest tests/test_foo.py -q`) rather than the whole tree.
2. If a run fails, capture the node id (`tests/test_foo.py::test_name`).
3. Re-run only that node: `pytest tests/test_foo.py::test_name -q --tb=short`.
4. Prefer the helper script if the failure output is noisy:

```bash
python /workspace/.agents/skills/pytest-debug/scripts/focus_failing_tests.py
```

5. Fix the **application code**, not the tests. Tests are read-only in this harness.
6. After a fix, re-run the failing node, then a broader `pytest tests -q -m "not slow"` if markers exist.

Read `references/traceback-reading.md` when the traceback is long or points at fixtures.
