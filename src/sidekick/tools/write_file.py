from pathlib import Path


async def write_file(filepath: str, content: str) -> str:
    """Write content to a file."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(content)

    return f"Successfully wrote to {filepath}"
