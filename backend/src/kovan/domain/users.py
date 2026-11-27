"""Kullanıcı (docs/domain-design.md § 2) ve kayıt kuralları R-01, R-02."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from kovan.domain.errors import DomainRuleError

MAX_EMAIL_LENGTH = 254
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


@dataclass(frozen=True)
class User:
    id: UUID
    email: str
    display_name: str
    password_hash: str
    created_at: datetime


def normalize_email(raw: str) -> str:
    """R-01: E-postayı doğrular ve küçük harfe çevirir (benzersizlik harf duyarsız)."""
    email = raw.strip().lower()
    if len(email) > MAX_EMAIL_LENGTH or not _looks_like_email(email):
        raise DomainRuleError(
            "E-posta adresi geçerli değil.", rule_code="R-01", code="EMAIL_INVALID"
        )
    return email


def _looks_like_email(email: str) -> bool:
    """Basit biçim kontrolü: tek "@", boşluk yok, alan adında baş ve son dışında en az bir nokta.

    Düzenli ifade yerine string işlemleri: Geri izleme (backtracking) riski yok.
    """
    local, _, domain = email.partition("@")
    if not local or "@" in domain or any(char.isspace() for char in email):
        return False
    return "." in domain[1:-1]


def check_password_length(password: str) -> None:
    """R-02: Şifre 8–128 karakter olmalı."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise DomainRuleError(
            f"Şifre en az {MIN_PASSWORD_LENGTH} karakter olmalı.",
            rule_code="R-02",
            code="PASSWORD_TOO_SHORT",
        )
    if len(password) > MAX_PASSWORD_LENGTH:
        raise DomainRuleError(
            f"Şifre en fazla {MAX_PASSWORD_LENGTH} karakter olabilir.",
            rule_code="R-02",
            code="PASSWORD_TOO_LONG",
        )
