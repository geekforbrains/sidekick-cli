async def read_file(filepath: str) -> str:
    """Read the contents of a file."""
    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()
        return content
