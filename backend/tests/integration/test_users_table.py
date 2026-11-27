"""users tablosu gerçek PostgreSQL'e karşı (#11, R-01)."""

import uuid

import pytest
from sqlalchemy import Engine, insert, select
from sqlalchemy.exc import IntegrityError

from kovan.infrastructure.db.tables import users


def new_user(email: str) -> dict[str, object]:
    return {
        "id": uuid.uuid4(),
        "email": email,
        "display_name": "Ayşe Y.",
        "password_hash": "$argon2id$v=19$m=65536,t=3,p=4$test",
    }


@pytest.mark.integration
def test_user_row_is_saved_with_created_at(clean_users: Engine) -> None:
    user = new_user("ayse@ornek.com")
    with clean_users.begin() as connection:
        connection.execute(insert(users).values(user))
        row = connection.execute(select(users).where(users.c.id == user["id"])).one()

    assert row.email == "ayse@ornek.com"
    assert row.created_at is not None


@pytest.mark.integration
def test_same_email_with_different_case_is_rejected(clean_users: Engine) -> None:
    with clean_users.begin() as connection:
        connection.execute(insert(users).values(new_user("ayse@ornek.com")))

    with pytest.raises(IntegrityError), clean_users.begin() as connection:
        connection.execute(insert(users).values(new_user("AYSE@Ornek.com")))
