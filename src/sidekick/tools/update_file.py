from pydantic_ai import ModelRetry


async def update_file(filepath: str, old_content: str, new_content: str) -> str:
    """Update specific content in a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
    except FileNotFoundError:
        raise ModelRetry(f"File not found: {filepath}. Please check the file path and try again.")
    except Exception as e:
        raise ModelRetry(f"Error reading file {filepath}: {str(e)}")

    if old_content not in content:
        # Provide helpful context about what was searched for
        preview = old_content[:100] + "..." if len(old_content) > 100 else old_content
        raise ModelRetry(
            f"Content to replace not found in {filepath}. "
            f"Searched for: '{preview}'. "
            "Please re-read the file and ensure the exact content matches, including whitespace."
        )

    try:
        updated_content = content.replace(old_content, new_content, 1)

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(updated_content)
    except Exception as e:
        raise ModelRetry(f"Error writing to file {filepath}: {str(e)}")

    return f"Successfully updated {filepath}"
