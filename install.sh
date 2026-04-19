#!/bin/bash
# hermes-qq-onebot installer wrapper
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/install.py" "$@"
