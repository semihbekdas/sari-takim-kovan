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

    def get_by_email(self, email: str) -> User | None:
        """Küçük harfe çevrilmiş e-postayla kullanıcıyı bulur; yoksa `None`."""
        ...

    def get_by_id(self, user_id: UUID) -> User | None:
        """Kimliğe göre kullanıcıyı bulur; yoksa `None`."""
        ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str:
        """Şifrenin Argon2id hash'ini döner (R-02, ADR-008)."""
        ...

    def verify(self, password_hash: str, password: str) -> bool:
        """Şifre hash'le eşleşiyorsa `True`, aksi halde `False` döner (hata fırlatmaz)."""
        ...


class SessionTokenService(Protocol):
    def issue(self, user_id: UUID) -> str:
        """Kullanıcı için imzalı, süreli bir oturum token'ı üretir (ADR-008)."""
        ...

    def read(self, token: str) -> UUID:
        """Token'daki kullanıcı kimliğini döner.

        Token geçersiz, bozuk veya süresi dolmuşsa `AuthenticationError` fırlatır.
        """
        ...
