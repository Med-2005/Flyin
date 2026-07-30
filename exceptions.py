"""Define custom errors for map validation and routing."""


class InvalidConfErr(Exception):
    """Raised when a map configuration is invalid."""

    pass


class NoPathError(Exception):
    """Raised when a drone has no valid route to its destination."""

    pass
