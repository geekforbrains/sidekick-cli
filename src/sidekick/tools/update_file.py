from sidekick import ui


async def update_file(filepath: str, old_content: str, new_content: str) -> str:
    """Update specific content in a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()

        if old_content not in content:
            err_msg = "Content to replace not found in file, re-read file and try again"
            await ui.error(err_msg)
            return err_msg

        updated_content = content.replace(old_content, new_content, 1)

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(updated_content)

        return f"Successfully updated {filepath}"
    except FileNotFoundError:
        err_msg = f"File not found: {filepath}"
        await ui.error(err_msg)
        return err_msg
    except Exception as e:
        err_msg = f"Error updating file: {str(e)}"
        await ui.error(err_msg)
        return err_msg
