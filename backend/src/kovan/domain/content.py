"""Sayfa içeriği (PageContent) kuralları — docs/domain-design.md § 4, R-06."""

import json
from typing import Any
from urllib.parse import urlsplit

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
ALLOWED_INLINE_TYPES = frozenset({"text", "link", "pageMention"})
ALLOWED_LINK_SCHEMES = frozenset({"http", "https"})
MAX_CONTENT_BYTES = 512 * 1024


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
    for item in block.get("content", []):
        check_inline(item)
    check_blocks(block.get("children", []))


def check_blocks(blocks: list[dict[str, Any]]) -> None:
    for block in blocks:
        check_block(block)


def check_content(blocks: list[dict[str, Any]]) -> None:
    size = len(json.dumps(blocks, ensure_ascii=False).encode("utf-8"))
    if size > MAX_CONTENT_BYTES:
        raise invalid_content("İçerik 512 KB'tan büyük olamaz.")
    check_blocks(blocks)


def check_inline(item: dict[str, Any]) -> None:
    item_type = item.get("type")
    if item_type not in ALLOWED_INLINE_TYPES:
        raise invalid_content(f"İzin verilmeyen satır içi tür: {item_type}")
    if item_type == "link":
        scheme = urlsplit(str(item.get("href", ""))).scheme.lower()
        if scheme not in ALLOWED_LINK_SCHEMES:
            raise invalid_content("Bağlantılar yalnızca http veya https olabilir.")


def to_plain_text(blocks: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for block in blocks:
        lines.append(inline_text(block.get("content", [])))
        lines.append(to_plain_text(block.get("children", [])))
    return "\n".join(line for line in lines if line)


def inline_text(items: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for item in items:
        if item.get("type") == "text":
            parts.append(str(item.get("text", "")))
        elif item.get("type") == "link":
            parts.append(inline_text(item.get("content", [])))
    return "".join(parts)
