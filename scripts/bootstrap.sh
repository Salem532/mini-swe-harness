#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "python: $(python3 --version)"
echo "uv: $(uv --version)"
if command -v docker >/dev/null; then
  docker version --format 'docker: {{.Server.Version}}'
else
  echo "docker: MISSING — install Docker Engine, then:"
  echo "  docker build -f docker/Dockerfile -t mini-swe-harness:local ."
fi
uv sync --extra dev
uv run pytest -q
echo "unit tests ok"
if [[ "${1:-}" == "--host" ]]; then
  uv sync --extra dev --extra host
  echo "mini-swe-agent extra installed"
fi
