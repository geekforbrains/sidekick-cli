# Backward compatibility imports
from .configuration.defaults import DEFAULT_USER_CONFIG
from .configuration.models import ModelRegistry
from .configuration.settings import ApplicationSettings

# Create global instances for backward compatibility
_app_settings = ApplicationSettings()
_model_registry = ModelRegistry()

# Export old interface
VERSION = _app_settings.version
NAME = _app_settings.name
GUIDE_FILE = _app_settings.guide_file
CONFIG_DIR = _app_settings.paths.config_dir
CONFIG_FILE = _app_settings.paths.config_file
DEFAULT_CONFIG = DEFAULT_USER_CONFIG
INTERNAL_TOOLS = _app_settings.internal_tools

# Convert new model structure to old dictionary format for compatibility
MODELS = {}
for name, config in _model_registry.list_models().items():
    MODELS[name] = {
        "pricing": {
            "input": config.pricing.input,
            "cached_input": config.pricing.cached_input,
            "output": config.pricing.output,
        }
    }
