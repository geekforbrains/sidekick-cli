import json
import os
import uuid
from pathlib import Path

import sentry_sdk

from sidekick import config, session
from sidekick.utils import ui


def _create_default_config():
    """Create the default configuration file."""
    if not config.CONFIG_DIR.exists():
        config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    with open(config.CONFIG_FILE, "w") as f:
        json.dump(config.DEFAULT_CONFIG, f, indent=2)

    return config.DEFAULT_CONFIG


def _load_config():
    """Load the user configuration file."""
    try:
        with open(config.CONFIG_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ui.warning(f"No config found or invalid JSON. Creating default at {config.CONFIG_FILE}\n")
        return _create_default_config()


def _setup_sentry():
    """Setup Sentry for error reporting if telemetry is enabled."""
    if not session.telemetry_enabled:
        return
    
    from sidekick import config
    
    # Determine environment based on whether we're running in development or production
    environment = "development" if config.IS_DEV else "production"
    
    sentry_sdk.init(
        dsn='https://c967e1bebffe899093ed6bc2ee2e90c7@o171515.ingest.us.sentry.io/4509084774105088',
        traces_sample_rate=0.1,  # Sample only 10% of transactions
        profiles_sample_rate=0.1,  # Sample only 10% of profiles
        send_default_pii=False,  # Don't send personally identifiable information
        before_send=before_send,  # Filter sensitive data
        environment=environment  # Set based on whether we're running from source or installed package
    )
    
    # Set user ID to anonymous session ID
    sentry_sdk.set_user({"id": session.session_id})


def before_send(event, hint):
    """Filter sensitive data from Sentry events."""
    # Don't send events if telemetry is disabled
    if not session.telemetry_enabled:
        return None
    
    # Filter out sensitive information
    if event.get("request") and event["request"].get("headers"):
        # Remove authorization headers
        headers = event["request"]["headers"]
        for key in list(headers.keys()):
            if key.lower() in ("authorization", "cookie", "x-api-key"):
                headers[key] = "[Filtered]"
    
    # Filter environment variables
    if event.get("extra") and event["extra"].get("sys.argv"):
        args = event["extra"]["sys.argv"]
        # Filter any arguments that might contain API keys
        for i, arg in enumerate(args):
            if "key" in arg.lower() or "token" in arg.lower() or "secret" in arg.lower():
                args[i] = "[Filtered]"
    
    # Filter message content to ensure no sensitive data is leaked
    if event.get("extra") and event["extra"].get("message"):
        # Remove potential sensitive content from messages
        event["extra"]["message"] = "[Content Filtered]"
    
    return event


def setup():
    """Handle setup operations for the application."""
    # Generate a unique session ID
    session.session_id = str(uuid.uuid4())
    
    # Load config
    session.user_config = _load_config()
    
    # Set up Sentry
    _setup_sentry()

    # Check for environment variables
    missing_keys = []
    provider_keys = session.user_config.get("env", {}).get("providers", {})
    for key, value in provider_keys.items():
        if not value and not os.getenv(key):
            missing_keys.append(key)

    if missing_keys:
        ui.warning("Missing environment variables or config values: " + ", ".join(missing_keys) + "\n")
        ui.status(
            "Either set these in your environment or update your config at ~/.config/sidekick.json\n"
        )

    # For each tool, check if the required environment variable is set
    tool_keys = session.user_config.get("env", {}).get("tools", {})
    missing_tools = []
    for key, value in tool_keys.items():
        # Only show warning if environment var is not set and config value is empty
        if not value and not os.getenv(key):
            missing_tools.append(key)

    if missing_tools:
        ui.warning("The following tools will not be available: " + ", ".join(missing_tools) + "\n")
