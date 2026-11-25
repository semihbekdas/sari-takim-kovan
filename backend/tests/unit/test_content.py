from typing import Any
from uuid import UUID

import pytest

from kovan.domain.content import PageContent
from kovan.domain.errors import DomainRuleError

A_PAGE = "3f1c2b6e-8d4a-4c1e-9b2f-1a2b3c4d5e6f"
B_PAGE = "9a2e7c10-5b3d-4f6a-8e9c-0d1e2f3a4b5c"


def text(value: str) -> dict[str, Any]:
    return {"type": "text", "text": value}


def mention(page_id: str) -> dict[str, Any]:
    return {"type": "pageMention", "props": {"pageId": page_id}}


def nested_blocks(depth: int) -> list[dict[str, Any]]:
    block: dict[str, Any] = {"type": "paragraph"}
    for _ in range(depth - 1):
        block = {"type": "paragraph", "children": [block]}
    return [block]


def assert_rejected(blocks: object) -> None:
    with pytest.raises(DomainRuleError) as error:
        PageContent(blocks)

    assert error.value.rule_code == "R-06"
    assert error.value.code == "CONTENT_INVALID"


# --- Kabul edilen içerik ---------------------------------------------------


@pytest.mark.parametrize(
    "blocks",
    [
        [],
        [{"type": "paragraph"}],
        [{"type": "heading", "props": {"level": 1}}],
        [{"type": "heading", "props": {"level": 3}}],
        [{"type": "paragraph", "content": [text("a"), mention(A_PAGE)]}],
        [{"type": "paragraph", "content": [{"type": "link", "href": "https://a.com"}]}],
        [{"type": "bulletListItem", "children": [{"type": "bulletListItem"}]}],
        nested_blocks(20),
    ],
)
def test_valid_content_is_kept_as_is(blocks: list[dict[str, Any]]) -> None:
    assert PageContent(blocks).blocks == blocks


def test_content_does_not_change_when_input_list_changes() -> None:
    blocks: list[dict[str, Any]] = [{"type": "paragraph"}]
    content = PageContent(blocks)

    blocks.append({"type": "quote"})

    assert content.blocks == [{"type": "paragraph"}]


def test_contents_with_same_blocks_are_equal() -> None:
    first = PageContent([{"type": "quote"}])
    second = PageContent([{"type": "quote"}])

    assert first == second
    assert first != PageContent([])


# --- Reddedilen içerik (R-06) ---------------------------------------------


@pytest.mark.ac("AC-04.4")
@pytest.mark.parametrize(
    "blocks",
    [
        [{"type": "table"}],
        [{"type": "heading", "props": {"level": 4}}],
        [{"type": "heading", "props": {"level": 0}}],
        [{"type": "heading"}],
        [{"type": "paragraph", "content": [{"type": "image"}]}],
        [{"type": "paragraph", "children": [{"type": "table"}]}],
    ],
)
def test_forbidden_types_are_rejected(blocks: object) -> None:
    assert_rejected(blocks)


@pytest.mark.ac("AC-04.4")
@pytest.mark.parametrize("href", ["javascript:alert(1)", "ftp://ornek.com", ""])
def test_link_that_is_not_http_or_https_is_rejected(href: str) -> None:
    assert_rejected([{"type": "paragraph", "content": [{"type": "link", "href": href}]}])


@pytest.mark.ac("AC-04.4")
def test_link_with_non_text_inside_is_rejected() -> None:
    link = {"type": "link", "href": "https://a.com", "content": [{"type": "image"}]}
    assert_rejected([{"type": "paragraph", "content": [link]}])


@pytest.mark.ac("AC-04.4")
@pytest.mark.parametrize(
    "blocks",
    [
        {"type": "paragraph"},
        ["düz metin"],
        [{"type": "heading", "props": None}],
        [{"type": "paragraph", "content": "abc"}],
        [{"type": "paragraph", "content": ["abc"]}],
        [{"type": "paragraph", "children": "abc"}],
        [{"type": "paragraph", "content": [{"type": "pageMention", "props": None}]}],
    ],
)
def test_unexpected_shapes_are_rejected(blocks: object) -> None:
    assert_rejected(blocks)


@pytest.mark.ac("AC-04.4")
@pytest.mark.parametrize("depth", [21, 3000])
def test_too_deep_nesting_is_rejected(depth: int) -> None:
    assert_rejected(nested_blocks(depth))


@pytest.mark.ac("AC-04.4")
def test_content_larger_than_512_kb_is_rejected() -> None:
    assert_rejected([{"type": "paragraph", "content": [text("a" * 512 * 1024)]}])


# --- Düz metin ------------------------------------------------------------


def test_plain_text_joins_blocks_line_by_line() -> None:
    link = {"type": "link", "href": "https://a.com", "content": [text("site")]}
    content = PageContent(
        [
            {"type": "heading", "props": {"level": 1}, "content": [text("Başlık")]},
            {"type": "paragraph", "content": [text("Bkz. "), link]},
        ]
    )

    assert content.to_plain_text() == "Başlık\nBkz. site"


def test_plain_text_includes_children_and_skips_empty_blocks() -> None:
    child = {"type": "bulletListItem", "content": [text("alt madde")]}
    content = PageContent(
        [
            {"type": "bulletListItem", "content": [text("madde")], "children": [child]},
            {"type": "paragraph", "content": []},
        ]
    )

    assert content.to_plain_text() == "madde\nalt madde"


def test_plain_text_of_empty_content_is_empty() -> None:
    assert PageContent([]).to_plain_text() == ""


# --- Sayfa bahisleri ------------------------------------------------------


def test_mentioned_page_ids_finds_mentions_in_blocks_and_children() -> None:
    child = {"type": "bulletListItem", "content": [mention(B_PAGE)]}
    content = PageContent(
        [
            {"type": "paragraph", "content": [mention(A_PAGE), mention(A_PAGE)]},
            {"type": "bulletListItem", "children": [child]},
        ]
    )

    assert content.mentioned_page_ids() == {UUID(A_PAGE), UUID(B_PAGE)}


def test_mentioned_page_ids_ignores_invalid_ids() -> None:
    content = PageContent([{"type": "paragraph", "content": [mention("bozuk")]}])

    assert content.mentioned_page_ids() == set()
