#!/usr/bin/env bash
set -e

echo "===================================================="
echo "RUNNING SOFTWARE DNA ENGINE AUTOMATED SELF-TEST"
echo "===================================================="

# Ensure workspace root is in PYTHONPATH
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

export PYTHONPATH="$ROOT_DIR/backend:$PYTHONPATH"

python "$ROOT_DIR/backend/run.py" --self-test
