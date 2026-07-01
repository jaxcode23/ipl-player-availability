class PlayerAvailabilityError(Exception):
    pass


class NotFoundError(PlayerAvailabilityError):
    pass


class CollectError(PlayerAvailabilityError):
    pass


class ParseError(PlayerAvailabilityError):
    pass


class NormalizeError(PlayerAvailabilityError):
    pass
