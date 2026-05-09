"""
QQ OneBot Platform Plugin for Hermes Agent.

Registers the QQ OneBot adapter with the plugin system.
The actual adapter implementation lives in qqonebot.py (same directory).
"""

import logging

logger = logging.getLogger(__name__)


def check_requirements() -> bool:
    """Check if QQ OneBot dependencies are available."""
    try:
        import websockets
        return True
    except ImportError:
        return False


def validate_config(config) -> bool:
    """Check if QQ OneBot is properly configured."""
    return config.enabled


def is_connected(config) -> bool:
    """Check if QQ OneBot is connected/enabled."""
    return config.enabled


def register(ctx):
    """Plugin entry point — called by the Hermes plugin system."""
    from qqonebot import QQAdapter, check_qq_requirements
    
    ctx.register_platform(
        name="qqonebot",
        label="QQ (OneBot)",
        adapter_factory=lambda cfg: QQAdapter(cfg),
        check_fn=check_qq_requirements,
        validate_config=validate_config,
        is_connected=is_connected,
        required_env=["QQ_ONEBOT_WS_URL"],
        install_hint="pip install websockets",
        # Auth env vars
        allowed_users_env="QQ_ONEBOT_ALLOWED_USERS",
        allow_all_env="QQ_ONEBOT_ALLOW_ALL_USERS",
        # QQ OneBot doesn't have strict message length limits
        max_message_length=0,
        # Display
        emoji="🐧",
        # QQ has user IDs that should be redacted
        pii_safe=False,
        allow_update_command=True,
        # LLM guidance
        platform_hint=(
            "You are chatting via QQ (OneBot protocol). "
            "Messages support text, images, voice, and file attachments. "
            "Keep responses concise and conversational."
        ),
    )
