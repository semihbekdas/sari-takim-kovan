import pytest

from kovan.application.auth_service import AuthService
from kovan.domain.errors import ConflictError, DomainRuleError
from tests.fakes import FakePasswordHasher, InMemoryUserRepository


@pytest.fixture
def users() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def service(users: InMemoryUserRepository) -> AuthService:
    return AuthService(users, FakePasswordHasher())


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
