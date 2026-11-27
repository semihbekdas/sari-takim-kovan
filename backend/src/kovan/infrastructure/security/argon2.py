"""`PasswordHasher` port'unun Argon2id uygulaması (ADR-008)."""

from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import InvalidHashError, VerificationError


class Argon2PasswordHasher:
    def __init__(self) -> None:
        # argon2-cffi varsayılanları Argon2id ve OWASP önerisine uygun parametrelerdir.
        self._hasher = Argon2Hasher()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password_hash: str, password: str) -> bool:
        try:
            return self._hasher.verify(password_hash, password)
        except (VerificationError, InvalidHashError):
            # Yanlış şifre (VerifyMismatchError, VerificationError'ın alt sınıfı) veya bozuk hash.
            return False
