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