class SidekickError(Exception):
    pass


class SidekickConfigError(SidekickError):
    pass


class SidekickAbort(Exception):
    """Exception raised to abort the current sidekick operation."""
    pass

