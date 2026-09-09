#!/usr/bin/env python3
"""Re-run only the last failing pytest node ids from a fresh collection."""

from __future__ import annotations

import re
import subprocess
import sys

FAILED = re.compile(r"^(FAILED|ERROR) (\S+?)(?: - |$)")


def main() -> int:
    listing = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        capture_output=True,
        text=True,
    )
    probe = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=line"],
        capture_output=True,
        text=True,
    )
    output = (probe.stdout or "") + (probe.stderr or "")
    nodes = []
    for line in output.splitlines():
        match = FAILED.search(line.strip())
        if match:
            nodes.append(match.group(2))
    if not nodes:
        sys.stdout.write(output)
        sys.stdout.write("\nNo FAILED node ids parsed; collected output follows.\n")
        sys.stdout.write(listing.stdout)
        return probe.returncode
    unique = list(dict.fromkeys(nodes))
    print("Re-running:", " ".join(unique))
    rerun = subprocess.run([sys.executable, "-m", "pytest", "-q", "--tb=short", *unique])
    return rerun.returncode


if __name__ == "__main__":
    raise SystemExit(main())
