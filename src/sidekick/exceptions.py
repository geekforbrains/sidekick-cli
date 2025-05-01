class SidekickError(Exception):
    pass


class SidekickConfigError(SidekickError):
    pass


class SidekickAbort(SidekickError):
    pass
