from pathlib import Path

from sidekick.constants import (APP_NAME, APP_VERSION, CONFIG_FILE_NAME, TOOL_READ_FILE,
                                TOOL_RUN_COMMAND, TOOL_UPDATE_FILE, TOOL_WRITE_FILE)
from sidekick.types import ConfigFile, ConfigPath, ToolName


class PathConfig:
    def __init__(self):
        self.config_dir: ConfigPath = Path.home() / ".config"
        self.config_file: ConfigFile = self.config_dir / CONFIG_FILE_NAME


class ApplicationSettings:
    def __init__(self):
        self.version = APP_VERSION
        self.name = APP_NAME
        self.guide_file = f"{self.name.upper()}.md"
        self.paths = PathConfig()
        self.internal_tools: list[ToolName] = [
            TOOL_READ_FILE,
            TOOL_RUN_COMMAND,
            TOOL_UPDATE_FILE,
            TOOL_WRITE_FILE,
        ]
