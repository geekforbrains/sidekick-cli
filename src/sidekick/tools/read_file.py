async def read_file(filepath: str) -> str:
    """Read the contents of a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
            return content
    except FileNotFoundError:
        return f"Error: File not found: {filepath}"
    except PermissionError:
        return f"Error: Permission denied: {filepath}"
    except Exception as e:
        return f"Error reading file {filepath}: {str(e)}"
