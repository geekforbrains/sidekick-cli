from pathlib import Path

from sidekick import ui


async def write_file(filepath: str, content: str) -> str:
    """Write content to a file."""
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(content)

        return f"Successfully wrote to {filepath}"
    except Exception as e:
        err_msg = f"Error writing file: {str(e)}"
        ui.error(err_msg)
        return err_msg
