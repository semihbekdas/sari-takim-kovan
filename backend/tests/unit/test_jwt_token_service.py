"""JwtTokenService (ADR-008: HS256, sub = user_id, 8 saat)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from kovan.application.auth_service import SESSION_LIFETIME
from kovan.application.errors import AuthenticationError
from kovan.infrastructure.security.jwt import JwtTokenService
from tests.fakes import TEST_JWT_SECRET


def make_service(clock_shift: timedelta = timedelta(0)) -> JwtTokenService:
    return JwtTokenService(
        TEST_JWT_SECRET, SESSION_LIFETIME, clock=lambda: datetime.now(UTC) + clock_shift
    )


def test_issued_token_is_hs256_with_user_id_and_eight_hour_lifetime() -> None:
    user_id = uuid4()

    token = make_service().issue(user_id)

    assert jwt.get_unverified_header(token)["alg"] == "HS256"
    claims = jwt.decode(token, TEST_JWT_SECRET, algorithms=["HS256"])
    assert claims["sub"] == str(user_id)
    assert claims["exp"] - claims["iat"] == 8 * 60 * 60


def test_read_returns_user_id_of_issued_token() -> None:
    service = make_service()
    user_id = uuid4()

    assert service.read(service.issue(user_id)) == user_id


@pytest.mark.ac("AC-02.4")
def test_expired_token_is_rejected() -> None:
    expired = make_service(clock_shift=-timedelta(hours=9)).issue(uuid4())

    with pytest.raises(AuthenticationError):
        make_service().read(expired)


@pytest.mark.parametrize(
    "token",
    [
        "bozuk-token",
        jwt.encode({"sub": "1", "exp": 4102444800}, "baska-bir-anahtar-ile-imzalanmis-token"),
        jwt.encode({"sub": "uuid-degil", "exp": 4102444800}, TEST_JWT_SECRET),
        jwt.encode({"sub": str(uuid4())}, TEST_JWT_SECRET),
        jwt.encode({"sub": str(uuid4()), "exp": 4102444800}, key=None, algorithm="none"),
    ],
    ids=["bozuk", "baska-anahtar", "sub-uuid-degil", "exp-yok", "alg-none"],
)
def test_invalid_tokens_are_rejected(token: str) -> None:
    with pytest.raises(AuthenticationError):
        make_service().read(token)
