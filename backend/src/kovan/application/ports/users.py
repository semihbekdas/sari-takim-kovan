"""Kullanıcı ve kimlik doğrulama port'ları."""

from typing import Protocol
from uuid import UUID

from kovan.domain.users import User


class UserRepository(Protocol):
    def add(self, *, user_id: UUID, email: str, display_name: str, password_hash: str) -> User:
        """Kullanıcıyı kaydeder ve `created_at` dolu haliyle döner.

        E-posta zaten kayıtlıysa `ConflictError(code="EMAIL_TAKEN")` fırlatır (R-01).
        """
        ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str:
        """Şifrenin Argon2id hash'ini döner (R-02, ADR-008)."""
        ...
