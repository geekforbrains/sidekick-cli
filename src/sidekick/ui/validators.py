"""Input validators for Sidekick UI."""

from prompt_toolkit.validation import ValidationError, Validator


class ModelValidator(Validator):
    """Validate default provider selection"""

    def __init__(self, index):
        self.index = index

    def validate(self, document) -> None:
        text = document.text.strip()
        if not text:
            raise ValidationError(message="Provider number cannot be empty")
        elif text and not text.isdigit():
            raise ValidationError(message="Invalid provider number")
        elif text.isdigit():
            number = int(text)
            if number < 0 or number >= self.index:
                raise ValidationError(
                    message="Invalid provider number",
                )
