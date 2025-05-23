from pathlib import Path


class PathConfig:
    def __init__(self):
        self.config_dir = Path.home() / ".config"
        self.config_file = self.config_dir / "sidekick.json"


class ApplicationSettings:
    def __init__(self):
        self.version = "0.4.1"
        self.name = "Sidekick"
        self.guide_file = f"{self.name.upper()}.md"
        self.paths = PathConfig()
        self.internal_tools = [
            "read_file",
            "run_command",
            "update_file",
            "write_file",
        ]
