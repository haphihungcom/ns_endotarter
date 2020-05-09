class EndotarterError(Exception):
    pass


class UserError(EndotarterError):
    pass


class AuthError(EndotarterError):
    pass


class NSSiteError(EndotarterError):
    pass