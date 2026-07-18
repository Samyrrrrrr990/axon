#!/usr/bin/env bash
# One-command Axon launcher: creates the environment if needed, starts the app.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
  echo "Axon uses uv to manage its Python environment."
  echo "Install it with:  curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

uv sync
exec uv run axon start "$@"
