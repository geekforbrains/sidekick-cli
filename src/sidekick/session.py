from . import config

user_config = {}
agents = {}
messages = []
total_cost = 0.0
current_model = config.default_model
spinner = None
tool_ignore = []  # Tools to ignore during confirmation
yolo = False  # Skip all confirmations if true
