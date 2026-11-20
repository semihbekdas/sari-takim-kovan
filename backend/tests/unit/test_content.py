import pytest

from kovan.domain.content import check_block
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
