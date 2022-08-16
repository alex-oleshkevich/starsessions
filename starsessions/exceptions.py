class SessionError(Exception):
    """Base class for session exceptions."""


class SessionNotLoaded(SessionError):
    """Raised on attempt to access/mutate session data of a session which has not been loaded yet."""

    solution = 'Call "starsessions.load_session(connection)" to load session data.'


class ImproperlyConfigured(SessionError):
    """Exception is raised when some settings are missing or misconfigured."""
