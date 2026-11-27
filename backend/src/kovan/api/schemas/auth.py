from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from kovan.domain.users import User


class RegisterRequest(BaseModel):
    # E-posta biçimi (R-01) ve şifre uzunluğu (R-02) domain'de kontrol edilir.
    email: str
    password: str
    display_name: str = Field(min_length=2, max_length=50)


class LoginRequest(BaseModel):
    # Biçim kontrolü yok: Hatalı e-posta da genel 401 alır (AC-02.2).
    email: str
    password: str


class UserResponse(BaseModel):
    """`password_hash` bilerek yok: Hiçbir yanıtta dışarı verilmez."""

    id: UUID
    email: str
    display_name: str
    created_at: datetime

    @classmethod
    def from_user(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            created_at=user.created_at,
        )
