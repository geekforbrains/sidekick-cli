# Backward compatibility imports
from .file_utils import DotDict, capture_stdout
from .text_utils import key_to_title, ext_to_lang
from .diff_utils import render_file_diff

# Re-export for backward compatibility
__all__ = ['DotDict', 'capture_stdout', 'key_to_title', 'ext_to_lang', 'render_file_diff']
