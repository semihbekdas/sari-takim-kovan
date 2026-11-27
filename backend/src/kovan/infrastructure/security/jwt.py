"""`SessionTokenService` port'unun JWT uygulaması (ADR-008: HS256, `sub = user_id`)."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from kovan.application.errors import AuthenticationError

ALGORITHM = "HS256"
INVALID_SESSION_MESSAGE = "Oturumunuz geçersiz veya süresi dolmuş. Lütfen yeniden giriş yapın."


def _utc_now() -> datetime:
    return datetime.now(UTC)


class JwtTokenService:
    def __init__(
        self,
        secret: str,
        lifetime: timedelta,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._secret = secret
        self._lifetime = lifetime
        self._clock = clock

    def issue(self, user_id: UUID) -> str:
        issued_at = self._clock()
        claims = {"sub": str(user_id), "iat": issued_at, "exp": issued_at + self._lifetime}
        return jwt.encode(claims, self._secret, algorithm=ALGORITHM)

    def read(self, token: str) -> UUID:
        try:
            # Yalnızca HS256 kabul edilir ("alg: none" gibi saldırılara karşı).
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[ALGORITHM],
                options={"require": ["sub", "exp"]},
            )
            return UUID(claims["sub"])
        except (jwt.InvalidTokenError, ValueError) as error:
            # Süresi dolmuş, imzası bozuk veya `sub`'ı UUID olmayan token.
            raise AuthenticationError(INVALID_SESSION_MESSAGE) from error
