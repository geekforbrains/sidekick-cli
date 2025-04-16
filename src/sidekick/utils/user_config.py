import json

from sidekick import config, session


def load_config():
    """Load user config from file"""
    try:
        with open(config.CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return None


def save_config():
    """Save user config to file"""
    try:
        with open(config.CONFIG_FILE, "w") as f:
            json.dump(session.user_config, f, indent=4)
        return True
    except Exception:
        return False


def get_mcp_servers():
    """Retrieve MCP server configurations from user config"""
    return session.user_config.get("mcpServers", [])


def set_default_model(model_name):
    """Set the default model in the user config and save"""
    session.user_config["default_model"] = model_name
    return save_config()
