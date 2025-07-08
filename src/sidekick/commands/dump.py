"""Handle /dump command."""

from sidekick import ui

DUMP_FILE_PATH = "dump.log"


def recursive_expand(obj, indent=0):
    """Recursively expand objects to show their attributes."""
    indent_str = "  " * indent
    lines = []

    if isinstance(obj, (str, int, float, bool, type(None))):
        return repr(obj)

    if hasattr(obj, "isoformat"):
        return repr(obj)

    if isinstance(obj, (list, tuple)):
        if not obj:
            return "[]" if isinstance(obj, list) else "()"

        bracket_open = "[" if isinstance(obj, list) else "("
        bracket_close = "]" if isinstance(obj, list) else ")"

        if len(obj) == 1 and isinstance(obj[0], (str, int, float, bool)):
            return f"{bracket_open}{repr(obj[0])}{bracket_close}"

        lines.append(bracket_open)
        for item in obj:
            expanded = recursive_expand(item, indent + 1)
            lines.append(f"{indent_str}  {expanded},")
        lines.append(f"{indent_str}{bracket_close}")
        return "\n".join(lines)

    if isinstance(obj, dict):
        if not obj:
            return "{}"

        lines.append("{")
        for key, value in obj.items():
            expanded_value = recursive_expand(value, indent + 1)
            lines.append(f"{indent_str}  {repr(key)}: {expanded_value},")
        lines.append(f"{indent_str}}}")
        return "\n".join(lines)

    if hasattr(obj, "__dict__"):
        class_name = type(obj).__name__
        attrs = vars(obj)

        if not attrs:
            return f"{class_name}()"

        lines.append(f"{class_name}(")
        for key, value in attrs.items():
            expanded_value = recursive_expand(value, indent + 1)
            lines.append(f"{indent_str}  {key}={expanded_value},")
        lines.append(f"{indent_str})")
        return "\n".join(lines)

    if hasattr(obj, "__class__"):
        class_name = type(obj).__name__
        attrs = {
            attr: getattr(obj, attr)
            for attr in dir(obj)
            if not attr.startswith("_") and not callable(getattr(obj, attr))
        }

        if not attrs:
            return repr(obj)

        lines.append(f"{class_name}(")
        for key, value in attrs.items():
            expanded_value = recursive_expand(value, indent + 1)
            lines.append(f"{indent_str}  {key}={expanded_value},")
        lines.append(f"{indent_str})")
        return "\n".join(lines)

    return repr(obj)


async def handle_dump(message_history):
    """Handle /dump command - write message history to dump.log, overwriting the file each time."""
    if not message_history:
        ui.error("Message history not available")
        return

    try:
        with open(DUMP_FILE_PATH, "w") as f:
            for i, message in enumerate(message_history):
                f.write(f"{'=' * 80}\n")
                f.write(f"Message #{i} - Type: {type(message).__name__}\n")
                f.write(f"{'=' * 80}\n\n")

                expanded = recursive_expand(message)
                f.write(expanded)
                f.write("\n\n")

        ui.success(f"Message history dumped to {DUMP_FILE_PATH}")
    except Exception as e:
        ui.error(f"Failed to dump message history: {e}")
