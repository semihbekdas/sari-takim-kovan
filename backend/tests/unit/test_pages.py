"""Page aggregate'i: R-03 başlık, R-07 sürüm çakışması, R-10/R-11 indeks alanları."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from kovan.domain.content import PageContent
from kovan.domain.errors import ConflictError, DomainRuleError
from kovan.domain.pages import (
    MAX_INDEX_ATTEMPTS,
    MAX_TITLE_LENGTH,
    UNTITLED,
    IndexStatus,
    Page,
    normalize_title,
)

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
LATER = NOW + timedelta(minutes=5)
EMPTY = PageContent([])
PARAGRAPH = PageContent([{"type": "paragraph", "content": [{"type": "text", "text": "Merhaba"}]}])


def new_page(title: str | None = "Dersler") -> Page:
    return Page.create(owner_id=uuid4(), parent_id=None, title=title, content=EMPTY, now=NOW)


# R-03 — başlık


@pytest.mark.parametrize("raw", [None, "", "   ", "\n\t"])
def test_missing_or_blank_title_becomes_untitled(raw: str | None) -> None:
    assert normalize_title(raw) == UNTITLED


def test_title_is_trimmed() -> None:
    assert normalize_title("  Veritabanı  ") == "Veritabanı"


def test_title_of_exactly_200_characters_is_allowed() -> None:
    title = "a" * MAX_TITLE_LENGTH

    assert normalize_title(title) == title


def test_title_longer_than_200_characters_is_rejected() -> None:
    with pytest.raises(DomainRuleError) as caught:
        normalize_title("a" * (MAX_TITLE_LENGTH + 1))

    assert caught.value.rule_code == "R-03"
    assert caught.value.code == "TITLE_TOO_LONG"


def test_length_is_checked_after_trimming() -> None:
    title = " " * 10 + "a" * MAX_TITLE_LENGTH + " " * 10

    assert normalize_title(title) == "a" * MAX_TITLE_LENGTH


# Oluşturma


def test_new_page_starts_at_version_1_and_is_not_indexed_yet() -> None:
    page = new_page(title=None)

    assert page.title == UNTITLED
    assert page.version == 1
    assert page.created_at == page.updated_at == NOW
    assert page.deleted_at is None
    assert page.indexed_version is None
    assert page.index_status is IndexStatus.PENDING


def test_each_new_page_gets_its_own_id() -> None:
    first = new_page()
    second = new_page()

    assert first.id != second.id


# Kaydetme — R-07, R-10, R-11


def test_edit_with_current_version_saves_and_increments_version() -> None:
    page = new_page()

    saved = page.edit(title="Yeni başlık", content=PARAGRAPH, expected_version=1, now=LATER)

    assert saved.title == "Yeni başlık"
    assert saved.content == PARAGRAPH
    assert saved.version == 2
    assert saved.updated_at == LATER
    assert saved.created_at == NOW
    assert saved.id == page.id


def test_edit_does_not_change_the_original_page() -> None:
    page = new_page()

    page.edit(title="Yeni", content=PARAGRAPH, expected_version=1, now=LATER)

    assert page.title == "Dersler"
    assert page.version == 1


def test_edit_with_stale_version_is_a_conflict() -> None:
    page = new_page().edit(title="İkinci", content=EMPTY, expected_version=1, now=LATER)

    with pytest.raises(ConflictError) as caught:
        page.edit(title="Eski sekme", content=EMPTY, expected_version=1, now=LATER)

    assert caught.value.code == "VERSION_CONFLICT"
    assert caught.value.rule_code == "R-07"


def test_edit_applies_title_rules() -> None:
    page = new_page()

    assert page.edit(title="  ", content=EMPTY, expected_version=1, now=LATER).title == UNTITLED
    with pytest.raises(DomainRuleError):
        page.edit(title="a" * 201, content=EMPTY, expected_version=1, now=LATER)


def test_edit_makes_an_indexed_page_pending_again() -> None:
    page = replace(new_page(), indexed_version=1)
    assert page.index_status is IndexStatus.INDEXED

    saved = page.edit(title="Dersler", content=PARAGRAPH, expected_version=1, now=LATER)

    assert saved.index_status is IndexStatus.PENDING


def test_edit_resets_failed_indexing_counters() -> None:
    failed = replace(
        new_page(),
        index_attempts=MAX_INDEX_ATTEMPTS,
        index_error="timeout",
        index_retry_at=LATER,
    )
    assert failed.index_status is IndexStatus.FAILED

    saved = failed.edit(title="Dersler", content=EMPTY, expected_version=1, now=LATER)

    assert saved.index_attempts == 0
    assert saved.index_error is None
    assert saved.index_retry_at is None
    assert saved.index_status is IndexStatus.PENDING


# İndeks durumu


def test_index_status_is_pending_below_the_attempt_limit() -> None:
    page = replace(new_page(), index_attempts=MAX_INDEX_ATTEMPTS - 1)

    assert page.index_status is IndexStatus.PENDING


def test_index_status_is_indexed_when_the_current_version_is_indexed() -> None:
    page = replace(new_page(), indexed_version=1, index_attempts=MAX_INDEX_ATTEMPTS)

    assert page.index_status is IndexStatus.INDEXED
