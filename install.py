#!/usr/bin/env python3
"""
hermes-qq-onebot installer (plugin mode)
Installs QQ OneBot v11 platform adapter as a Hermes plugin.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

HERMES_HOME = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")))
HERMES_AGENT = HERMES_HOME / "hermes-agent"
PLUGINS_DIR = HERMES_HOME / "plugins"
SCRIPT_DIR = Path(__file__).parent

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

def info(msg): print(f"{CYAN}▸{RESET} {msg}")
def ok(msg):   print(f"{GREEN}✔{RESET} {msg}")
def warn(msg): print(f"{YELLOW}⚠{RESET} {msg}")
def fail(msg): print(f"{RED}✘{RESET} {msg}")

def check_hermes():
    """Check if hermes-agent is installed."""
    if not HERMES_AGENT.is_dir():
        fail(f"Hermes agent not found at {HERMES_AGENT}")
        fail("Please install hermes-agent first: https://github.com/NousResearch/hermes-agent")
        return False
    if not (HERMES_AGENT / "run_agent.py").is_file():
        fail(f"Invalid hermes-agent installation at {HERMES_AGENT}")
        return False
    return True

def install_adapter():
    """Copy qq_adapter.py to hermes gateway platforms."""
    src = SCRIPT_DIR / "qq_adapter.py"
    dst = HERMES_AGENT / "gateway" / "platforms" / "qqonebot.py"
    
    if not src.is_file():
        fail(f"Adapter file not found: {src}")
        return False
    
    # Backup existing file
    if dst.is_file():
        backup = dst.with_suffix(".py.bak")
        if not backup.is_file():
            shutil.copy2(dst, backup)
            info(f"Backed up existing adapter: {backup.name}")
    
    shutil.copy2(src, dst)
    ok(f"Installed adapter: {dst}")
    return True

def install_plugin():
    """Copy plugin files to hermes plugins directory."""
    src = SCRIPT_DIR / "plugins" / "qqonebot"
    dst = PLUGINS_DIR / "qqonebot"
    
    if not src.is_dir():
        fail(f"Plugin directory not found: {src}")
        return False
    
    # Backup existing plugin
    if dst.is_dir():
        backup = dst.with_name("qqonebot.bak")
        if backup.is_dir():
            shutil.rmtree(backup)
        shutil.move(str(dst), str(backup))
        info(f"Backed up existing plugin: {backup.name}")
    
    shutil.copytree(src, dst)
    ok(f"Installed plugin: {dst}")
    return True

def enable_plugin():
    """Enable the qqonebot plugin."""
    try:
        result = subprocess.run(
            ["hermes", "plugins", "enable", "qqonebot"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            ok("Plugin enabled")
            return True
        else:
            warn(f"Could not enable plugin: {result.stderr}")
            info("Run manually: hermes plugins enable qqonebot")
            return False
    except FileNotFoundError:
        warn("hermes command not found")
        info("Run manually: hermes plugins enable qqonebot")
        return False

def install_deps():
    """Install Python dependencies."""
    try:
        import websockets
        ok("websockets already installed")
        return True
    except ImportError:
        info("Installing websockets...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "websockets"], check=True)
            ok("websockets installed")
            return True
        except subprocess.CalledProcessError:
            fail("Failed to install websockets")
            info("Run manually: pip install websockets")
            return False

def main():
    print(f"\n{BOLD}hermes-qq-onebot Installer (Plugin Mode){RESET}\n")
    
    if not check_hermes():
        return 1
    
    info(f"Hermes home: {HERMES_HOME}")
    info(f"Hermes agent: {HERMES_AGENT}")
    print()
    
    # Install adapter
    info("Installing QQ OneBot adapter...")
    if not install_adapter():
        return 1
    
    # Install plugin
    info("Installing plugin...")
    if not install_plugin():
        return 1
    
    # Enable plugin
    info("Enabling plugin...")
    enable_plugin()
    
    # Install dependencies
    info("Checking dependencies...")
    install_deps()
    
    print()
    ok("Installation complete!")
    print()
    info("Next steps:")
    print("  1. Add qqonebot platform to ~/.hermes/config.yaml:")
    print()
    print("     platforms:")
    print("       qqonebot:")
    print("         enabled: true")
    print("         extra:")
    print('           http_api_url: "http://127.0.0.1:5700"')
    print("           reverse_mode: true")
    print('           reverse_host: "0.0.0.0"')
    print("           reverse_port: 6700")
    print()
    print("  2. Restart gateway: hermes gateway restart")
    print()
    
    return 0

def uninstall():
    """Uninstall the QQ OneBot plugin."""
    print(f"\n{BOLD}hermes-qq-onebot Uninstaller{RESET}\n")
    
    # Disable plugin
    info("Disabling plugin...")
    try:
        subprocess.run(["hermes", "plugins", "disable", "qqonebot"], capture_output=True)
    except FileNotFoundError:
        pass
    
    # Remove adapter
    adapter = HERMES_AGENT / "gateway" / "platforms" / "qqonebot.py"
    if adapter.is_file():
        adapter.unlink()
        ok(f"Removed adapter: {adapter}")
    
    # Restore backup if exists
    backup = adapter.with_suffix(".py.bak")
    if backup.is_file():
        shutil.move(str(backup), str(adapter))
        info(f"Restored backup: {adapter}")
    
    # Remove plugin
    plugin = PLUGINS_DIR / "qqonebot"
    if plugin.is_dir():
        shutil.rmtree(plugin)
        ok(f"Removed plugin: {plugin}")
    
    # Restore plugin backup if exists
    plugin_backup = plugin.with_name("qqonebot.bak")
    if plugin_backup.is_dir():
        shutil.move(str(plugin_backup), str(plugin))
        info(f"Restored plugin backup: {plugin}")
    
    print()
    ok("Uninstallation complete!")
    print()
    info("Restart gateway: hermes gateway restart")
    
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        sys.exit(uninstall())
    else:
        sys.exit(main())
