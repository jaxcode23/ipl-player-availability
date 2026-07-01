from ..exceptions import NormalizeError


class UnhandledRecordError(NormalizeError):
    pass


class ValidationError(NormalizeError):
    pass


class UnresolvedPlayerError(NormalizeError):
    pass
