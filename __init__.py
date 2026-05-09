"""Plugin entry point — exports register function."""

import sys
from pathlib import Path

# Ensure plugin directory is in sys.path so adapter.py can import qqonebot
_plugin_dir = str(Path(__file__).parent)
if _plugin_dir not in sys.path:
    sys.path.insert(0, _plugin_dir)

from .adapter import register

__all__ = ["register"]
