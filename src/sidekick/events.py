from enum import Enum

from sidekick import session


class Event(Enum):
    """
    Enum for event names.
    """
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


def emit(event: Event, *args, **kwargs):
    """
    Emit an event with the given name and arguments.
    """
    handlers = session.event_handlers.get(event, [])
    for handler in handlers:
        handler(*args, **kwargs)


def subscribe(event: Event, handler):
    """
    Subscribe a handler to an event.
    """
    session.event_handlers.setdefault(event, []).append(handler)


def success(message: str):
    emit(Event.SUCCESS, message=message)
