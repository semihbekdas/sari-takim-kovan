"""Kayıt ve oturum işlemleri (US-01, US-02)."""

from datetime import timedelta
from uuid import uuid4

from kovan.application.errors import AuthenticationError
from kovan.application.ports.users import PasswordHasher, SessionTokenService, UserRepository
from kovan.domain.users import User, check_password_length, normalize_email

# ADR-008: Oturum 8 saat geçerlidir; süre dolunca kullanıcı yeniden giriş yapar.
SESSION_LIFETIME = timedelta(hours=8)

# AC-02.2: Hangi bilginin yanlış olduğu söylenmez.
INVALID_CREDENTIALS_MESSAGE = "E-posta veya şifre hatalı."
UNAUTHENTICATED_MESSAGE = "Bu işlem için giriş yapmalısınız."

# Kullanıcı bulunamadığında da bir hash doğrulanır; böylece yanıt süresinden
# e-postanın kayıtlı olup olmadığı anlaşılmaz.
_TIMING_DUMMY_PASSWORD = "kovan-timing-dummy-password"  # noqa: S105 (gizli değil)


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        tokens: SessionTokenService,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens
        self._dummy_hash = hasher.hash(_TIMING_DUMMY_PASSWORD)

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

    def login(self, *, email: str, password: str) -> str:
        """Bilgiler doğruysa oturum token'ı döner (AC-02.1).

        E-posta yoksa veya şifre yanlışsa aynı genel hata verilir (AC-02.2).
        """
        user = self._users.get_by_email(email.strip().lower())
        password_hash = user.password_hash if user else self._dummy_hash
        password_matches = self._hasher.verify(password_hash, password)
        if user is None or not password_matches:
            raise AuthenticationError(INVALID_CREDENTIALS_MESSAGE, code="INVALID_CREDENTIALS")
        return self._tokens.issue(user.id)

    def current_user(self, token: str | None) -> User:
        """Oturum token'ının sahibini döner; token yoksa veya geçersizse 401 (AC-02.4)."""
        if not token:
            raise AuthenticationError(UNAUTHENTICATED_MESSAGE)
        # Geçersiz veya süresi dolmuş token'da `read` AuthenticationError fırlatır.
        user = self._users.get_by_id(self._tokens.read(token))
        if user is None:
            # Token geçerli ama kullanıcı artık yok: Oturum geçersiz sayılır.
            raise AuthenticationError(UNAUTHENTICATED_MESSAGE)
        return user
