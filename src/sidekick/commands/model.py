"""Handle /model command."""

import logging

from rich.table import Table

from sidekick import ui
from sidekick.config import update_config_file
from sidekick.constants import MODELS
from sidekick.session import session

log = logging.getLogger(__name__)


async def handle_model(args: list[str]):
    """Handle /model command - list, switch, or set default model."""
    if len(args) == 0:
        table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
        table.add_column("#", justify="right", style=ui.colors.primary)
        table.add_column("Model", style="white")

        for i, model_name in enumerate(MODELS.keys(), 1):
            label = model_name
            if model_name == session.current_model:
                label += " [dim](current)[/dim]"
            table.add_row(str(i), label)

        ui.info_panel(table, "Available Models")

    elif len(args) >= 1:
        try:
            model_num = int(args[0])
            model_list = list(MODELS.keys())
            if 1 <= model_num <= len(model_list):
                selected_model = model_list[model_num - 1]

                if len(args) >= 2 and args[1] == "default":
                    try:
                        update_config_file({"default_model": selected_model})
                        ui.success(f"Set {selected_model} as default model")
                    except Exception as e:
                        ui.error(f"Failed to update config: {e}")
                else:
                    old_model = session.current_model
                    session.current_model = selected_model
                    log.debug(f"Model switched from {old_model} to {selected_model}")
                    ui.info(f"Switched to model: {selected_model}")
            else:
                ui.error(f"Invalid model number. Choose between 1 and {len(model_list)}")
        except ValueError:
            ui.error("Invalid model number")
