import typing


class SessionMetadata(typing.TypedDict):
    lifetime: int
    created: float  # timestamp
    last_access: float  # timestamp
    last_update: float  # timestamp
