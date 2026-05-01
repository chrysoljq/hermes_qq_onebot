#!/bin/bash
# Uninstall hermes-qq-onebot plugin
set -e
cd "$(dirname "$0")"
python3 install.py uninstall
