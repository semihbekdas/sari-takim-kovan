"""`SqlPageRepository` gerçek PostgreSQL'e karşı (#9; R-04, R-07, R-08).

Her test geri alınan bir işlem içinde çalışır (`db_connection`, conftest.py).
"""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Connection, insert
from sqlalchemy.exc import IntegrityError

from kovan.domain.content import PageContent
from kovan.domain.errors import ConflictError
from kovan.domain.pages import Page
from kovan.infrastructure.db.page_repository import SqlPageRepository
from kovan.infrastructure.db.tables import users

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)
CONTENT = PageContent([{"type": "paragraph", "content": [{"type": "text", "text": "Merhaba"}]}])


def add_user(connection: Connection) -> UUID:
    user_id = uuid4()
    connection.execute(
        insert(users).values(
            id=user_id,
            email=f"{user_id}@ornek.com",
            display_name="Test",
            password_hash="$argon2id$test",
        )
    )
    return user_id


def new_page(owner_id: UUID, parent_id: UUID | None = None) -> Page:
    return Page.create(
        owner_id=owner_id, parent_id=parent_id, title="Dersler", content=CONTENT, now=NOW
    )


@pytest.fixture
def repo(db_connection: Connection) -> SqlPageRepository:
    return SqlPageRepository(db_connection)


@pytest.fixture
def owner(db_connection: Connection) -> UUID:
    return add_user(db_connection)


def test_added_page_is_read_back_with_all_fields(repo: SqlPageRepository, owner: UUID) -> None:
    page = new_page(owner)
    repo.add(page)

    assert repo.get(owner_id=owner, page_id=page.id) == page


def test_child_page_keeps_its_parent(repo: SqlPageRepository, owner: UUID) -> None:
    parent = new_page(owner)
    child = new_page(owner, parent_id=parent.id)
    repo.add(parent)
    repo.add(child)

    found = repo.get(owner_id=owner, page_id=child.id)

    assert found is not None
    assert found.parent_id == parent.id


def test_missing_page_is_none(repo: SqlPageRepository, owner: UUID) -> None:
    assert repo.get(owner_id=owner, page_id=uuid4()) is None


def test_other_users_page_is_not_visible(
    repo: SqlPageRepository, owner: UUID, db_connection: Connection
) -> None:
    page = new_page(owner)
    repo.add(page)
    stranger = add_user(db_connection)

    assert repo.get(owner_id=stranger, page_id=page.id) is None  # R-04


def test_deleted_page_is_not_returned(repo: SqlPageRepository, owner: UUID) -> None:
    page = replace(new_page(owner), deleted_at=NOW)
    repo.add(page)

    assert repo.get(owner_id=owner, page_id=page.id) is None  # R-08


def test_page_of_unknown_user_is_rejected(repo: SqlPageRepository) -> None:
    with pytest.raises(IntegrityError):
        repo.add(new_page(owner_id=uuid4()))


def test_update_with_current_version_saves_the_new_version(
    repo: SqlPageRepository, owner: UUID
) -> None:
    page = new_page(owner)
    repo.add(page)
    later = NOW + timedelta(minutes=1)
    edited = page.edit(title="Yeni başlık", content=PageContent([]), expected_version=1, now=later)

    repo.update(edited, expected_version=1)

    assert repo.get(owner_id=owner, page_id=page.id) == edited


def test_update_with_stale_version_is_a_conflict(repo: SqlPageRepository, owner: UUID) -> None:
    page = new_page(owner)
    repo.add(page)
    first = page.edit(title="İlk sekme", content=CONTENT, expected_version=1, now=NOW)
    repo.update(first, expected_version=1)
    second = page.edit(title="Eski sekme", content=CONTENT, expected_version=1, now=NOW)

    with pytest.raises(ConflictError) as caught:  # R-07
        repo.update(second, expected_version=1)

    assert caught.value.code == "VERSION_CONFLICT"
    found = repo.get(owner_id=owner, page_id=page.id)
    assert found is not None
    assert found.title == "İlk sekme"


def test_other_user_cannot_update_the_page(
    repo: SqlPageRepository, owner: UUID, db_connection: Connection
) -> None:
    page = new_page(owner)
    repo.add(page)
    stranger = add_user(db_connection)
    hijacked = replace(page, owner_id=stranger, title="Ele geçirildi", version=2)

    with pytest.raises(ConflictError):  # R-04: başkasının sayfası güncellenemez
        repo.update(hijacked, expected_version=1)

    found = repo.get(owner_id=owner, page_id=page.id)
    assert found is not None
    assert found.title == "Dersler"
