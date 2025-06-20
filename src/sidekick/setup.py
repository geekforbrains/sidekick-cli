import json
from pathlib import Path
from typing import Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from .config import deep_merge_dicts, ensure_config_structure
from .constants import DEFAULT_USER_CONFIG

console = Console()


def validate_json_file(config_path: Path) -> Optional[Dict]:
    """Validate if a JSON file is valid and return its content."""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def collect_api_keys() -> Dict[str, str]:
    """Collect API keys from user input."""
    console.print("\n[bold]API Keys Configuration[/bold]\n")
    console.print("Enter your API keys (press Enter to skip):\n")

    api_keys = {}
    providers = [
        ("ANTHROPIC_API_KEY", "Anthropic (Claude)"),
        ("OPENAI_API_KEY", "OpenAI (GPT)"),
        ("GEMINI_API_KEY", "Google (Gemini)"),
    ]

    for key, name in providers:
        value = Prompt.ask(f"{name} API Key", password=True, default="")
        if value:
            api_keys[key] = value

    return api_keys


def select_default_model(api_keys: Dict[str, str]) -> str:
    """Select default model based on available API keys."""
    available_models = []

    if "ANTHROPIC_API_KEY" in api_keys:
        available_models.extend(
            [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
            ]
        )

    if "OPENAI_API_KEY" in api_keys:
        available_models.extend(
            [
                "gpt-4o",
                "gpt-4o-mini",
            ]
        )

    if "GEMINI_API_KEY" in api_keys:
        available_models.extend(
            [
                "gemini-2.0-flash-exp",
                "gemini-1.5-pro-latest",
            ]
        )

    if not available_models:
        console.print("[yellow]No API keys provided. Using default model.[/yellow]")
        return DEFAULT_USER_CONFIG["default_model"]

    console.print("\n[bold]Default Model Selection[/bold]\n")
    for i, model in enumerate(available_models, 1):
        console.print(f"{i}. {model}")

    while True:
        choice = Prompt.ask(
            "\nSelect default model", choices=[str(i) for i in range(1, len(available_models) + 1)]
        )
        return available_models[int(choice) - 1]


def create_config(config_path: Path) -> Dict:
    """Create a new configuration file."""
    console.print(
        Panel.fit(
            "[bold cyan]Sidekick CLI Setup[/bold cyan]\n\n"
            "Welcome! Let's set up your configuration.",
            border_style="cyan",
        )
    )

    api_keys = collect_api_keys()

    if not api_keys:
        console.print("\n[red]No API keys provided. At least one API key is required.[/red]")
        if not Confirm.ask("Continue anyway?", default=False):
            raise KeyboardInterrupt("Setup cancelled")

    default_model = select_default_model(api_keys)

    # Start with user's choices
    user_config = {"default_model": default_model, "env": api_keys if api_keys else {}}

    # Merge with defaults to get all fields
    config = deep_merge_dicts(DEFAULT_USER_CONFIG, user_config)

    # Remove placeholder API keys if user didn't provide any
    if not api_keys:
        config["env"] = {}

    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    console.print(f"\n[green]✓ Configuration saved to {config_path}[/green]")

    return config


def handle_invalid_config(config_path: Path) -> Dict:
    """Handle invalid configuration file."""
    console.print(
        Panel.fit(
            "[bold red]Invalid Configuration File[/bold red]\n\n"
            f"The configuration file at {config_path} is invalid or corrupted.",
            border_style="red",
        )
    )

    console.print("\nOptions:")
    console.print("1. Reset configuration (create new)")
    console.print("2. Exit and fix manually")

    choice = Prompt.ask("\nWhat would you like to do?", choices=["1", "2"])

    if choice == "1":
        config_path.unlink()
        return create_config(config_path)
    else:
        raise SystemExit("Please fix the configuration file manually and try again.")


def run_setup() -> Dict:
    """Run the setup flow and return the configuration."""
    config_path = Path.home() / ".config" / "sidekick.json"

    if config_path.exists():
        config = validate_json_file(config_path)
        if config is None:
            return handle_invalid_config(config_path)

        required_fields = ["default_model", "env"]
        if all(field in config for field in required_fields):
            # Ensure all default fields are present
            return ensure_config_structure()
        else:
            console.print("[yellow]Configuration file is missing required fields.[/yellow]")
            return handle_invalid_config(config_path)

    return create_config(config_path)
