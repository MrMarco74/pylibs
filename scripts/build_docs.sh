#!/usr/bin/env bash
# Generates static HTML API reference from docstrings via pdoc.
# Requires the `dev` extra: pip install -e ".[dev]"
set -euo pipefail

cd "$(dirname "$0")/.."

pdoc --output-directory docs/html src/pylibs

echo "Docs built at docs/html/index.html"
