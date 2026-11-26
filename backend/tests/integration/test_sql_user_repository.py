"""SqlUserRepository gerçek PostgreSQL'e karşı (#11, R-01)."""

import uuid

import pytest
from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError

from kovan.domain.errors import ConflictError
from kovan.infrastructure.db.users import SqlUserRepository


def add_user(repository: SqlUserRepository, email: str) -> None:
    repository.add(
        user_id=uuid.uuid4(), email=email, display_name="Ayşe", password_hash="$argon2id$test"
    )


@pytest.mark.integration
def test_add_returns_user_with_created_at(clean_users: Engine) -> None:
    user_id = uuid.uuid4()

    user = SqlUserRepository(clean_users).add(
        user_id=user_id, email="ayse@ornek.com", display_name="Ayşe", password_hash="$argon2id$x"
    )

    assert user.id == user_id
    assert user.email == "ayse@ornek.com"
    assert user.created_at.tzinfo is not None


@pytest.mark.integration
def test_add_with_taken_email_raises_email_taken(clean_users: Engine) -> None:
    repository = SqlUserRepository(clean_users)
    add_user(repository, "ayse@ornek.com")

    with pytest.raises(ConflictError) as error:
        add_user(repository, "ayse@ornek.com")

    assert error.value.code == "EMAIL_TAKEN"


@pytest.mark.integration
def test_other_integrity_errors_are_not_reported_as_email_taken(clean_users: Engine) -> None:
    repository = SqlUserRepository(clean_users)
    user_id = uuid.uuid4()
    repository.add(user_id=user_id, email="a@ornek.com", display_name="Ayşe", password_hash="h")

    with pytest.raises(IntegrityError):
        repository.add(user_id=user_id, email="b@ornek.com", display_name="Ayşe", password_hash="h")


@pytest.mark.integration
def test_get_by_email_and_id_find_saved_user(clean_users: Engine) -> None:
    repository = SqlUserRepository(clean_users)
    user = repository.add(
        user_id=uuid.uuid4(), email="ayse@ornek.com", display_name="Ayşe", password_hash="h"
    )

    assert repository.get_by_email("ayse@ornek.com") == user
    assert repository.get_by_id(user.id) == user


@pytest.mark.integration
def test_get_returns_none_for_unknown_user(clean_users: Engine) -> None:
    repository = SqlUserRepository(clean_users)

    assert repository.get_by_email("yok@ornek.com") is None
    assert repository.get_by_id(uuid.uuid4()) is None
