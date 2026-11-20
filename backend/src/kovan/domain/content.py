"""Sayfa içeriği (PageContent) kuralları — docs/domain-design.md § 4, R-06."""

from typing import Any

from kovan.domain.errors import DomainRuleError

ALLOWED_BLOCK_TYPES = frozenset(
    {
        "paragraph",
        "heading",
        "bulletListItem",
        "numberedListItem",
        "checkListItem",
        "codeBlock",
        "quote",
    }
)
ALLOWED_HEADING_LEVELS = frozenset({1, 2, 3})


def invalid_content(message: str) -> DomainRuleError:
    return DomainRuleError(message, rule_code="R-06", code="CONTENT_INVALID")


def check_block(block: dict[str, Any]) -> None:
    block_type = block.get("type")
    if block_type not in ALLOWED_BLOCK_TYPES:
        raise invalid_content(f"İzin verilmeyen blok türü: {block_type}")
    if block_type == "heading":
        level = block.get("props", {}).get("level")
        if level not in ALLOWED_HEADING_LEVELS:
            raise invalid_content("Başlık seviyesi 1, 2 veya 3 olmalı.")
