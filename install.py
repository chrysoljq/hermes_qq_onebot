#!/usr/bin/env python3
"""
hermes-qq-onebot installer
Patches hermes-agent to add QQ OneBot v11 platform support.
"""

import os
import sys
import re
import shutil
import subprocess
from pathlib import Path

HERMES_DIR = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes/hermes-agent"))
SCRIPT_DIR = Path(__file__).parent
PATCHES_DIR = SCRIPT_DIR / "patches"

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

def find_hermes_dir():
    """Auto-detect hermes-agent installation."""
    candidates = [
        os.environ.get("HERMES_HOME"),
        os.path.expanduser("~/.hermes/hermes-agent"),
        os.path.expanduser("~/hermes-agent"),
    ]
    for d in candidates:
        if d and os.path.isdir(d) and os.path.isfile(os.path.join(d, "run_agent.py")):
            return d
    return None

def backup_file(path):
    """Create .bak backup before patching."""
    bak = path + ".bak"
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
        info(f"Backed up: {os.path.basename(path)}")
    else:
        info(f"Backup exists: {os.path.basename(path)}.bak")

def patch_enum_platform(path):
    """Add Platform.QQ enum value after Platform.QQBOT."""
    with open(path, "r") as f:
        content = f.read()

    if "QQ = \"qq\"" in content:
        warn("Platform.QQ already exists in config.py, skipping enum patch")
        return False

    backup_file(path)
    content = content.replace(
        '    QQBOT = "qqbot"',
        '    QQBOT = "qqbot"\n    QQ = "qq"'
    )
    with open(path, "w") as f:
        f.write(content)
    ok("Patched Platform enum")
    return True

def patch_config_connected(path):
    """Add QQ to get_connected_platforms validation."""
    with open(path, "r") as f:
        content = f.read()

    if 'platform == Platform.QQ and config.enabled' in content:
        warn("QQ connected-platform check already exists, skipping")
        return False

    backup_file(path)
    # Insert after the dingtalk connected check block
    old = '                connected.append(platform)\n        \n        return connected'
    new = '                connected.append(platform)\n            elif platform == Platform.QQ and config.enabled and config.extra.get("api_port"):\n                connected.append(platform)\n        \n        return connected'
    if old not in content:
        fail("Cannot find insertion point for QQ connected check in config.py")
        return False
    content = content.replace(old, new, 1)
    with open(path, "w") as f:
        f.write(content)
    ok("Patched get_connected_platforms")
    return True

def patch_config_env_overrides(path):
    """Add QQ OneBot env override block."""
    with open(path, "r") as f:
        content = f.read()

    if "qq_onebot_enabled" in content:
        warn("QQ OneBot env overrides already exist, skipping")
        return False

    backup_file(path)
    block = '''
    # QQ OneBot v11 (NapCat/go-cqhttp/Lagrange)
    qq_onebot_enabled = os.getenv("QQ_ONEBOT_ENABLED", "").lower() in ("true", "1", "yes")
    qq_onebot_api = os.getenv("QQ_ONEBOT_API_URL", "").strip()
    if qq_onebot_enabled or qq_onebot_api:
        if Platform.QQ not in config.platforms:
            config.platforms[Platform.QQ] = PlatformConfig()
        config.platforms[Platform.QQ].enabled = True
        qq_extra = config.platforms[Platform.QQ].extra
        if qq_onebot_api:
            from urllib.parse import urlparse
            parsed = urlparse(qq_onebot_api)
            qq_extra["api_host"] = parsed.hostname or "127.0.0.1"
            qq_extra["api_port"] = parsed.port or 5700
        qq_extra["listen_host"] = os.getenv("QQ_ONEBOT_LISTEN_HOST", qq_extra.get("listen_host", "127.0.0.1"))
        listen_port = os.getenv("QQ_ONEBOT_LISTEN_PORT", "")
        if listen_port:
            qq_extra["listen_port"] = int(listen_port)
        else:
            qq_extra.setdefault("listen_port", 5701)
        qq_extra["access_token"] = os.getenv("QQ_ONEBOT_ACCESS_TOKEN", qq_extra.get("access_token", ""))
        qq_extra["secret"] = os.getenv("QQ_ONEBOT_SECRET", qq_extra.get("secret", ""))
        qq_extra["allowed_qq_ids"] = os.getenv("QQ_ONEBOT_ALLOWED_USERS", qq_extra.get("allowed_qq_ids", ""))
        qq_extra["allow_all_users"] = os.getenv("QQ_ONEBOT_ALLOW_ALL", "").lower() in ("true", "1", "yes") or qq_extra.get("allow_all_users", False)
        qq_home = os.getenv("QQ_ONEBOT_HOME_CHANNEL", "").strip()
        if qq_home:
            config.platforms[Platform.QQ].home_channel = HomeChannel(
                platform=Platform.QQ,
                chat_id=qq_home,
                name=os.getenv("QQ_ONEBOT_HOME_CHANNEL_NAME", "Home"),
            )
'''
    # Insert before session settings comment
    marker = '    # Session settings'
    if marker not in content:
        fail("Cannot find '# Session settings' marker in config.py")
        return False
    content = content.replace(marker, block + marker)
    with open(path, "w") as f:
        f.write(content)
    ok("Patched env overrides for QQ OneBot")
    return True

def patch_run_py(path):
    """Patch gateway/run.py with QQ OneBot adapter instantiation."""
    with open(path, "r") as f:
        content = f.read()

    if "from gateway.platforms.qq import QQAdapter as QQOneBotAdapter" in content:
        warn("run.py already patched for QQ, skipping")
        return False

    backup_file(path)

    # 1. Add QQ_ONEBOT_ALLOWED_USERS to the allowlist env vars
    content = content.replace(
        '                       "QQ_ALLOWED_USERS",\n                       "GATEWAY_ALLOWED_USERS")',
        '                       "QQ_ALLOWED_USERS",\n                       "QQ_ONEBOT_ALLOWED_USERS",\n                       "GATEWAY_ALLOWED_USERS")'
    )

    # 2. Add QQ_ONEBOT_ALLOW_ALL
    content = content.replace(
        '                       "QQ_ALLOW_ALL_USERS")',
        '                       "QQ_ALLOW_ALL_USERS",\n                       "QQ_ONEBOT_ALLOW_ALL")'
    )

    # 3. Add QQ adapter instantiation after QQBot block
    old = """            return QQAdapter(config)

        return None"""
    new = """            return QQAdapter(config)

        elif platform == Platform.QQ:
            from gateway.platforms.qq import QQAdapter as QQOneBotAdapter, check_qq_requirements as check_qq_ob_requirements
            if not check_qq_ob_requirements():
                logger.warning("QQ OneBot: websockets not installed")
                return None
            return QQOneBotAdapter(config)

        return None"""
    if old not in content:
        fail("Cannot find QQBot adapter block in run.py")
        return False
    content = content.replace(old, new, 1)

    # 4. Add Platform.QQ to user env map
    content = content.replace(
        '            Platform.QQBOT: "QQ_ALLOWED_USERS",',
        '            Platform.QQBOT: "QQ_ALLOWED_USERS",\n            Platform.QQ: "QQ_ONEBOT_ALLOWED_USERS",'
    )

    # 5. Add Platform.QQ to allow-all env map
    content = content.replace(
        '            Platform.QQBOT: "QQ_ALLOW_ALL_USERS",',
        '            Platform.QQBOT: "QQ_ALLOW_ALL_USERS",\n            Platform.QQ: "QQ_ONEBOT_ALLOW_ALL",'
    )

    with open(path, "w") as f:
        f.write(content)
    ok("Patched gateway/run.py")
    return True

def patch_platforms_py(path):
    """Add QQ to CLI platforms list."""
    with open(path, "r") as f:
        content = f.read()

    if '"qq"' in content and 'OneBot' in content:
        warn("hermes_cli/platforms.py already has QQ, skipping")
        return False

    backup_file(path)
    content = content.replace(
        '    ("qqbot",          PlatformInfo(label="💬 QQBot",           default_toolset="hermes-qqbot")),',
        '    ("qqbot",          PlatformInfo(label="💬 QQBot",           default_toolset="hermes-qqbot")),\n    ("qq",             PlatformInfo(label="💬 QQ (OneBot)",     default_toolset="hermes-qq")),'
    )
    with open(path, "w") as f:
        f.write(content)
    ok("Patched hermes_cli/platforms.py")
    return True

def patch_gateway_py(path):
    """Add QQ OneBot setup wizard config."""
    with open(path, "r") as f:
        content = f.read()

    if '"qq"' in content and 'OneBot' in content:
        warn("hermes_cli/gateway.py already has QQ setup, skipping")
        return False

    backup_file(path)
    block = '''    {
        "key": "qq",
        "label": "QQ (OneBot v11)",
        "emoji": "💬",
        "token_var": "QQ_ONEBOT_API_URL",
        "setup_instructions": [
            "1. Install a OneBot v11 implementation (NapCatQQ recommended)",
            "2. Start the OneBot implementation — it listens on port 5700 by default",
            "3. Configure the OneBot implementation to send events to port 5701",
        ],
        "vars": [
            {"name": "QQ_ONEBOT_ENABLED", "prompt": "Enable QQ OneBot adapter? (yes/no)", "password": False},
            {"name": "QQ_ONEBOT_API_URL", "prompt": "OneBot HTTP API URL (e.g., http://127.0.0.1:5700)", "password": False,
             "help": "URL of your NapCat/go-cqhttp HTTP API endpoint."},
            {"name": "QQ_ONEBOT_LISTEN_PORT", "prompt": "Adapter listen port for events (default 5701)", "password": False},
            {"name": "QQ_ONEBOT_ACCESS_TOKEN", "prompt": "OneBot access_token (or empty)", "password": True,
             "help": "Optional Bearer token for OneBot API authentication."},
            {"name": "QQ_ONEBOT_SECRET", "prompt": "OneBot event secret for HMAC (or empty)", "password": True},
            {"name": "QQ_ONEBOT_ALLOWED_USERS", "prompt": "Allowed QQ IDs (comma-separated, or empty for all)", "password": False,
             "is_allowlist": True},
            {"name": "QQ_ONEBOT_HOME_CHANNEL", "prompt": "Home group ID for cron delivery (or empty)", "password": False},
        ],
    },
'''
    # Insert before the closing ] of _PLATFORMS
    marker = ']'
    # Find the last occurrence that closes _PLATFORMS (after the dingtalk/weixin block)
    # Look for the pattern with help key and then closing bracket
    idx = content.rfind('        ],\n    },\n]')
    if idx == -1:
        fail("Cannot find _PLATFORMS closing bracket in gateway.py")
        return False
    content = content[:idx+len('        ],\n    },')] + block + content[idx+len('        ],\n    },'):]
    with open(path, "w") as f:
        f.write(content)
    ok("Patched hermes_cli/gateway.py")
    return True

def patch_status_py(path):
    """Add QQ OneBot to status display."""
    with open(path, "r") as f:
        content = f.read()

    if "QQ OneBot" in content:
        warn("hermes_cli/status.py already has QQ OneBot, skipping")
        return False

    backup_file(path)
    content = content.replace(
        '        "QQBot": ("QQ_APP_ID", "QQBOT_HOME_CHANNEL"),',
        '        "QQBot": ("QQ_APP_ID", "QQBOT_HOME_CHANNEL"),\n        "QQ OneBot": ("QQ_ONEBOT_API_URL", "QQ_ONEBOT_HOME_CHANNEL"),'
    )
    with open(path, "w") as f:
        f.write(content)
    ok("Patched hermes_cli/status.py")
    return True

def patch_toolsets_py(path):
    """Add hermes-qq toolset definition."""
    with open(path, "r") as f:
        content = f.read()

    if '"hermes-qq"' in content:
        warn("hermes-qq toolset already exists, skipping")
        return False

    backup_file(path)

    # Add hermes-qq toolset after hermes-qqbot
    old = '    "hermes-qqbot": {\n        "description": "QQBot toolset - QQ messaging via official bot API (full access)",\n        "tools": _HERMES_CORE_TOOLS,\n        "includes": []\n    },\n\n    "hermes-wecom":'
    new = '    "hermes-qqbot": {\n        "description": "QQBot toolset - QQ messaging via official bot API (full access)",\n        "tools": _HERMES_CORE_TOOLS,\n        "includes": []\n    },\n\n    "hermes-qq": {\n        "description": "QQ OneBot v11 toolset - QQ messaging via NapCat/go-cqhttp (full access)",\n        "tools": _HERMES_CORE_TOOLS,\n        "includes": []\n    },\n\n    "hermes-wecom":'
    if old not in content:
        # Try alternate pattern
        old2 = '    "hermes-qqbot": {'
        if old2 not in content:
            fail("Cannot find hermes-qqbot toolset in toolsets.py")
            return False
        # Find the closing of hermes-qqbot
        idx = content.find(old2)
        close_idx = content.find("},", idx) + 2
        # Insert after hermes-qqbot
        content = content[:close_idx] + '\n\n    "hermes-qq": {\n        "description": "QQ OneBot v11 toolset - QQ messaging via NapCat/go-cqhttp (full access)",\n        "tools": _HERMES_CORE_TOOLS,\n        "includes": []\n    },' + content[close_idx:]
    else:
        content = content.replace(old, new)

    # Add hermes-qq to hermes-gateway includes
    content = content.replace(
        '"hermes-qqbot", "hermes-webhook"]',
        '"hermes-qqbot", "hermes-qq", "hermes-webhook"]'
    )

    with open(path, "w") as f:
        f.write(content)
    ok("Patched toolsets.py")
    return True

def patch_init_py(path):
    """Add QQAdapter import to __init__.py."""
    with open(path, "r") as f:
        content = f.read()

    if "from .qq import QQAdapter" in content:
        warn("__init__.py already has QQ import, skipping")
        return False

    backup_file(path)

    # Only add if qqbot import exists (to place it correctly)
    if "from .qqbot import QQAdapter" in content:
        content = content.replace(
            "from .qqbot import QQAdapter",
            "from .qqbot import QQAdapter\nfrom .qq import QQAdapter as QQOneBotAdapter"
        )
        content = content.replace(
            '    "QQAdapter",',
            '    "QQAdapter",\n    "QQOneBotAdapter",'
        )
    else:
        # Insert before __all__
        content = content.replace(
            '__all__ = [',
            'from .qq import QQAdapter as QQOneBotAdapter\n\n__all__ = [\n    "QQOneBotAdapter",'
        )

    with open(path, "w") as f:
        f.write(content)
    ok("Patched __init__.py")
    return True

def copy_adapter(hermes_dir):
    """Copy qq_adapter.py to gateway/platforms/qq.py."""
    dest = os.path.join(hermes_dir, "gateway", "platforms", "qq.py")
    src = SCRIPT_DIR / "qq_adapter.py"
    if os.path.exists(dest):
        # Check if same content
        with open(src, "rb") as f1, open(dest, "rb") as f2:
            if f1.read() == f2.read():
                warn("qq.py already installed and up to date")
                return False
    backup_file(dest) if os.path.exists(dest) else None
    shutil.copy2(src, dest)
    ok("Installed gateway/platforms/qq.py")
    return True

def install_websockets(hermes_dir):
    """Install websockets in the hermes venv."""
    venv_pip = os.path.join(hermes_dir, "venv", "bin", "pip")
    if os.path.exists(venv_pip):
        info("Installing websockets in hermes venv...")
        ret = subprocess.run([venv_pip, "install", "-q", "websockets"],
                           capture_output=True, text=True)
        if ret.returncode == 0:
            ok("websockets installed")
        else:
            warn(f"pip install websockets failed: {ret.stderr.strip()}")
    else:
        warn("Could not find hermes venv pip, please run: pip install websockets")

def do_uninstall(hermes_dir):
    """Restore all backed up files and remove qq.py."""
    info("Uninstalling hermes-qq-onebot...")
    qq_path = os.path.join(hermes_dir, "gateway", "platforms", "qq.py")
    if os.path.exists(qq_path):
        os.remove(qq_path)
        ok("Removed gateway/platforms/qq.py")

    for fname in [
        "gateway/config.py",
        "gateway/run.py",
        "gateway/platforms/__init__.py",
        "hermes_cli/platforms.py",
        "hermes_cli/gateway.py",
        "hermes_cli/status.py",
        "toolsets.py",
    ]:
        path = os.path.join(hermes_dir, fname)
        bak = path + ".bak"
        if os.path.exists(bak):
            shutil.copy2(bak, path)
            os.remove(bak)
            ok(f"Restored {fname}")
    ok("Uninstall complete. Restart hermes gateway.")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        hermes_dir = find_hermes_dir()
        if not hermes_dir:
            fail("Could not find hermes-agent installation")
            sys.exit(1)
        do_uninstall(hermes_dir)
        return

    print(f"\n{BOLD}hermes-qq-onebot installer{RESET}\n")

    hermes_dir = find_hermes_dir()
    if not hermes_dir:
        fail("Could not find hermes-agent installation.")
        info("Set HERMES_HOME env var or install to ~/.hermes/hermes-agent")
        sys.exit(1)

    info(f"Hermes directory: {hermes_dir}")

    # Verify it's a hermes installation
    if not os.path.isfile(os.path.join(hermes_dir, "run_agent.py")):
        fail("Directory does not look like hermes-agent (no run_agent.py)")
        sys.exit(1)

    changed = False

    # Copy adapter file
    changed |= copy_adapter(hermes_dir)

    # Patch files
    patches = [
        ("gateway/config.py",      [patch_enum_platform, patch_config_connected, patch_config_env_overrides]),
        ("gateway/run.py",          [patch_run_py]),
        ("gateway/platforms/__init__.py", [patch_init_py]),
        ("hermes_cli/platforms.py", [patch_platforms_py]),
        ("hermes_cli/gateway.py",   [patch_gateway_py]),
        ("hermes_cli/status.py",    [patch_status_py]),
        ("toolsets.py",             [patch_toolsets_py]),
    ]

    for relpath, patch_fns in patches:
        path = os.path.join(hermes_dir, relpath)
        if not os.path.exists(path):
            fail(f"File not found: {relpath}")
            continue
        for fn in patch_fns:
            try:
                changed |= fn(path)
            except Exception as e:
                fail(f"Error patching {relpath}: {e}")

    # Install dependency
    install_websockets(hermes_dir)

    print()
    if changed:
        ok("Installation complete!")
        print(f"\n  {BOLD}Next steps:{RESET}")
        print(f"  1. Add QQ config to ~/.hermes/config.yaml or set env vars")
        print(f"  2. Restart hermes gateway: hermes gateway restart")
        print(f"  3. Run ./install.sh uninstall to remove\n")
    else:
        info("Everything already installed, nothing to do.")

if __name__ == "__main__":
    main()
