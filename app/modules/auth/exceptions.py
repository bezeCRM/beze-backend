from __future__ import annotations


class AuthError(Exception):
    pass


class InvalidCredentials(AuthError):
    pass


class LoginAlreadyExists(AuthError):
    pass


class TokenInvalid(AuthError):
    pass


class TokenRevoked(AuthError):
    pass