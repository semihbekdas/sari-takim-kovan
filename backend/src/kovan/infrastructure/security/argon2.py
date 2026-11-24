"""`PasswordHasher` port'unun Argon2id uygulaması (ADR-008)."""

from argon2 import PasswordHasher as Argon2Hasher


class Argon2PasswordHasher:
    def __init__(self) -> None:
        # argon2-cffi varsayılanları Argon2id ve OWASP önerisine uygun parametrelerdir.
        self._hasher = Argon2Hasher()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)
