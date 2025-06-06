from sidekick import ui


async def read_file(filepath: str) -> str:
    """Read the contents of a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
            return content
    except FileNotFoundError:
        err_msg = f"File not found: {filepath}"
        await ui.error(err_msg)
        return err_msg
    except Exception as e:
        err_msg = f"Error reading file: {str(e)}"
        await ui.error(err_msg)
        return err_msg
