class DiscoveryError(Exception):
    def __init__(self, code: str, message: str, **details: object):
        super().__init__(message)
        self.code = code
        self.details = details


def require(condition: object, code: str, message: str, **details: object) -> None:
    if not condition:
        raise DiscoveryError(code, message, **details)
