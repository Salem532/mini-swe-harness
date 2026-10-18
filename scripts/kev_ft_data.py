#!/usr/bin/env python3
"""Build the product `block` fine-tune set. Writes evals/cache/kev-ft/*.jsonl (gitignored)."""

from __future__ import annotations

import json
import sys

from mini_swe_harness.kev_ft import build_dataset


def main() -> int:
    try:
        manifest = build_dataset()
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 2
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
