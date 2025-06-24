async def update_file(filepath: str, old_content: str, new_content: str) -> str:
    """Update specific content in a file."""
    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()

    if old_content not in content:
        raise ValueError("Content to replace not found in file, re-read file and try again")

    updated_content = content.replace(old_content, new_content, 1)

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(updated_content)

    return f"Successfully updated {filepath}"
