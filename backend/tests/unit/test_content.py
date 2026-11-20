import pytest

from kovan.domain.content import check_block, check_content, to_plain_text
from kovan.domain.errors import DomainRuleError


def test_paragraph_block_is_allowed() -> None:
    check_block({"type": "paragraph"})


@pytest.mark.ac("AC-04.4")
def test_table_block_is_rejected() -> None:
    with pytest.raises(DomainRuleError) as error:
        check_block({"type": "table"})

    assert error.value.rule_code == "R-06"
    assert error.value.code == "CONTENT_INVALID"


@pytest.mark.parametrize("level", [1, 2, 3])
def test_heading_level_1_to_3_is_allowed(level: int) -> None:
    check_block({"type": "heading", "props": {"level": level}})


@pytest.mark.ac("AC-04.4")
@pytest.mark.parametrize("level", [0, 4, None])
def test_other_heading_levels_are_rejected(level: int | None) -> None:
    with pytest.raises(DomainRuleError):
        check_block({"type": "heading", "props": {"level": level}})


def test_paragraph_with_text_link_and_mention_is_allowed() -> None:
    check_block(
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "Merhaba"},
                {"type": "link", "href": "https://ornek.com", "content": []},
                {"type": "pageMention", "props": {"pageId": "9a2e"}},
            ],
        }
    )


@pytest.mark.ac("AC-04.4")
def test_unknown_inline_type_is_rejected() -> None:
    with pytest.raises(DomainRuleError):
        check_block({"type": "paragraph", "content": [{"type": "image"}]})


@pytest.mark.ac("AC-04.4")
@pytest.mark.parametrize("href", ["javascript:alert(1)", "ftp://ornek.com", ""])
def test_link_that_is_not_http_or_https_is_rejected(href: str) -> None:
    link = {"type": "link", "href": href, "content": []}
    with pytest.raises(DomainRuleError):
        check_block({"type": "paragraph", "content": [link]})


def test_valid_nested_list_is_allowed() -> None:
    child = {"type": "bulletListItem", "content": [{"type": "text", "text": "alt"}]}
    check_content([{"type": "bulletListItem", "children": [child]}])


@pytest.mark.ac("AC-04.4")
def test_forbidden_block_inside_children_is_rejected() -> None:
    with pytest.raises(DomainRuleError):
        check_content([{"type": "paragraph", "children": [{"type": "table"}]}])


def test_empty_content_is_allowed() -> None:
    check_content([])


@pytest.mark.ac("AC-04.4")
def test_content_larger_than_512_kb_is_rejected() -> None:
    big_text = {"type": "text", "text": "a" * (512 * 1024)}
    with pytest.raises(DomainRuleError) as error:
        check_content([{"type": "paragraph", "content": [big_text]}])

    assert error.value.rule_code == "R-06"


def test_plain_text_joins_blocks_line_by_line() -> None:
    link = {
        "type": "link",
        "href": "https://ornek.com",
        "content": [{"type": "text", "text": "site"}],
    }
    text = to_plain_text(
        [
            {"type": "heading", "content": [{"type": "text", "text": "Başlık"}]},
            {"type": "paragraph", "content": [{"type": "text", "text": "Bkz. "}, link]},
        ]
    )

    assert text == "Başlık\nBkz. site"


def test_plain_text_includes_children_and_skips_empty_blocks() -> None:
    child = {"type": "bulletListItem", "content": [{"type": "text", "text": "alt madde"}]}
    text = to_plain_text(
        [
            {
                "type": "bulletListItem",
                "content": [{"type": "text", "text": "madde"}],
                "children": [child],
            },
            {"type": "paragraph", "content": []},
        ]
    )

    assert text == "madde\nalt madde"


def test_plain_text_of_empty_content_is_empty() -> None:
    assert to_plain_text([]) == ""
