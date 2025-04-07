import uuid

user_config = {}
agents = {}
messages = []
total_cost = 0.0
current_model = ""  # Will be set from user_config after setup
spinner = None
tool_ignore = []  # Tools to ignore during confirmation
yolo = False  # Skip all confirmations if true
undo_initialized = False  # Whether the undo system has been initialized
session_id = str(uuid.uuid4())  # Unique ID for the current session
device_id = None  # Unique ID for the device, loaded during initialization
telemetry_enabled = True
