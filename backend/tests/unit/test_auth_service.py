from uuid import uuid4

import pytest

from kovan.application.auth_service import INVALID_CREDENTIALS_MESSAGE, AuthService
from kovan.application.errors import AuthenticationError
from kovan.domain.errors import ConflictError, DomainRuleError
from tests.fakes import FakePasswordHasher, FakeSessionTokenService, InMemoryUserRepository

PASSWORD = "gizli-sifre"


@pytest.fixture
def users() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def service(users: InMemoryUserRepository) -> AuthService:
    return AuthService(users, FakePasswordHasher(), FakeSessionTokenService())


def test_register_saves_lowercased_email_and_hashed_password(
    service: AuthService, users: InMemoryUserRepository
) -> None:
    user = service.register(email="Ayse@Ornek.com", password="gizli-sifre", display_name="Ayşe")

    assert user.email == "ayse@ornek.com"
    assert user.display_name == "Ayşe"
    assert user.password_hash == "hashed:gizli-sifre"
    assert users.users == [user]


@pytest.mark.ac("AC-01.3")
def test_register_with_short_password_saves_nothing(
    service: AuthService, users: InMemoryUserRepository
) -> None:
    with pytest.raises(DomainRuleError) as error:
        service.register(email="ayse@ornek.com", password="kisa", display_name="Ayşe")

    assert error.value.rule_code == "R-02"
    assert users.users == []


@pytest.mark.ac("AC-01.3")
def test_register_with_invalid_email_saves_nothing(
    service: AuthService, users: InMemoryUserRepository
) -> None:
    with pytest.raises(DomainRuleError) as error:
        service.register(email="ayse", password="gizli-sifre", display_name="Ayşe")

    assert error.value.rule_code == "R-01"
    assert users.users == []


@pytest.mark.ac("AC-01.2")
def test_register_with_same_email_in_other_case_is_conflict(service: AuthService) -> None:
    service.register(email="Ayse@Ornek.com", password="gizli-sifre", display_name="Ayşe")

    with pytest.raises(ConflictError) as error:
        service.register(email="ayse@ornek.com", password="baska-sifre", display_name="Ayşe 2")

    assert error.value.code == "EMAIL_TAKEN"


@pytest.mark.ac("AC-02.1")
def test_login_with_correct_credentials_returns_token_of_that_user(service: AuthService) -> None:
    user = service.register(email="ayse@ornek.com", password=PASSWORD, display_name="Ayşe")

    token = service.login(email=" Ayse@Ornek.com ", password=PASSWORD)

    assert service.current_user(token) == user


@pytest.mark.ac("AC-02.2")
@pytest.mark.parametrize(
    ("email", "password"),
    [("ayse@ornek.com", "yanlis-sifre"), ("yok@ornek.com", PASSWORD), ("gecersiz", PASSWORD)],
)
def test_login_with_wrong_email_or_password_gives_same_generic_error(
    service: AuthService, email: str, password: str
) -> None:
    service.register(email="ayse@ornek.com", password=PASSWORD, display_name="Ayşe")

    with pytest.raises(AuthenticationError) as error:
        service.login(email=email, password=password)

    assert error.value.code == "INVALID_CREDENTIALS"
    assert error.value.message == INVALID_CREDENTIALS_MESSAGE


@pytest.mark.ac("AC-02.4")
@pytest.mark.parametrize("token", [None, "", "bozuk-token"])
def test_current_user_without_valid_token_is_unauthenticated(
    service: AuthService, token: str | None
) -> None:
    with pytest.raises(AuthenticationError) as error:
        service.current_user(token)

    assert error.value.code == "UNAUTHENTICATED"


def test_current_user_of_deleted_user_is_unauthenticated(service: AuthService) -> None:
    token = FakeSessionTokenService().issue(uuid4())

    with pytest.raises(AuthenticationError) as error:
        service.current_user(token)

    assert error.value.code == "UNAUTHENTICATED"
