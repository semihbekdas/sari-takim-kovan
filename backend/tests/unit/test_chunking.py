"""Sayfa parçalama (ADR-009)."""

from typing import Any

import pytest

from kovan.application.chunking import Chunk, chunk_page
from kovan.domain.content import PageContent


def heading(level: int, value: str) -> dict[str, Any]:
    return {
        "type": "heading",
        "props": {"level": level},
        "content": [{"type": "text", "text": value}],
    }


def paragraph(value: str) -> dict[str, Any]:
    return {"type": "paragraph", "content": [{"type": "text", "text": value}]}


def test_page_without_headings_is_one_chunk_under_page_title() -> None:
    content = PageContent([paragraph("birinci"), paragraph("ikinci")])

    assert chunk_page("Notlar", content) == [Chunk(heading_path="Notlar", text="birinci\nikinci")]


def test_heading_path_starts_with_page_title() -> None:
    content = PageContent([heading(1, "Normalizasyon"), heading(2, "3NF"), paragraph("tanım")])

    assert chunk_page("Veritabanı", content) == [
        Chunk(heading_path="Veritabanı › Normalizasyon › 3NF", text="tanım")
    ]


def test_empty_page_has_no_chunks() -> None:
    assert chunk_page("Boş", PageContent([])) == []
    assert chunk_page("Boş", PageContent([heading(1, "Yalnız başlık")])) == []


def test_new_chunk_starts_when_limit_would_be_exceeded() -> None:
    content = PageContent([paragraph("a" * 6), paragraph("b" * 3), paragraph("c" * 4)])

    chunks = chunk_page("S", content, max_chars=10)

    assert [chunk.text for chunk in chunks] == ["a" * 6 + "\n" + "b" * 3, "c" * 4]


def test_blocks_are_not_split_when_they_fit() -> None:
    content = PageContent([paragraph("x" * 7), paragraph("y" * 7)])

    assert [chunk.text for chunk in chunk_page("S", content, max_chars=10)] == ["x" * 7, "y" * 7]


def test_very_long_block_is_split_into_fixed_length_pieces() -> None:
    content = PageContent([paragraph("k" * 25)])

    chunks = chunk_page("S", content, max_chars=10)

    assert [chunk.text for chunk in chunks] == ["k" * 10, "k" * 10, "k" * 5]
    assert all(len(chunk.text) <= 10 for chunk in chunks)


def test_default_limit_is_1000_characters() -> None:
    content = PageContent([paragraph("d" * 1500)])

    assert [len(chunk.text) for chunk in chunk_page("S", content)] == [1000, 500]


def test_turkish_characters_are_kept_and_counted_as_characters() -> None:
    content = PageContent([heading(1, "Çalışma Öğretisi"), paragraph("ığüşöç" * 2)])

    chunks = chunk_page("Ünite", content, max_chars=6)

    assert chunks == [
        Chunk(heading_path="Ünite › Çalışma Öğretisi", text="ığüşöç"),
        Chunk(heading_path="Ünite › Çalışma Öğretisi", text="ığüşöç"),
    ]


def test_limit_must_be_positive() -> None:
    with pytest.raises(ValueError, match="max_chars"):
        chunk_page("S", PageContent([]), max_chars=0)
