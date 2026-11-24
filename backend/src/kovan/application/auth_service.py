"""Kayıt ve oturum işlemleri (US-01, US-02)."""

from uuid import uuid4

from kovan.application.ports.users import PasswordHasher, UserRepository
from kovan.domain.users import User, check_password_length, normalize_email


class AuthService:
    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._hasher = hasher

    def register(self, *, email: str, password: str, display_name: str) -> User:
        """Yeni hesap açar. Şifre yalnızca hash'lenmiş olarak saklanır (R-02)."""
        normalized_email = normalize_email(email)
        check_password_length(password)
        return self._users.add(
            user_id=uuid4(),
            email=normalized_email,
            display_name=display_name,
            password_hash=self._hasher.hash(password),
        )
