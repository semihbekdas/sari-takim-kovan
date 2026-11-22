"""Sayfa içeriği (PageContent) değer nesnesi — docs/domain-design.md § 4, R-06."""

import copy
import json
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

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
MAX_BLOCK_DEPTH = 20


class PageContent:
    """Editörün blok dizisi. Oluşturulurken doğrulanır (R-06), sonra değişmez."""

    def __init__(self, blocks: object) -> None:
        checked = _check_blocks(blocks, depth=1)
        size = len(json.dumps(checked, ensure_ascii=False).encode("utf-8"))
        if size > MAX_CONTENT_BYTES:
            raise _invalid("İçerik 512 KB'tan büyük olamaz.")
        self._blocks: list[dict[str, Any]] = copy.deepcopy(checked)

    @property
    def blocks(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._blocks)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, PageContent) and self._blocks == other._blocks

    def to_plain_text(self) -> str:
        return _plain_text(self._blocks)

    def mentioned_page_ids(self) -> set[UUID]:
        return _mentioned_page_ids(self._blocks)


def _invalid(message: str) -> DomainRuleError:
    return DomainRuleError(message, rule_code="R-06", code="CONTENT_INVALID")


def _as_list(value: object, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise _invalid(f"{name} bir liste olmalı.")
    return value


def _as_dict(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _invalid(f"{name} bir nesne olmalı.")
    return value


def _check_blocks(blocks: object, depth: int) -> list[Any]:
    block_list = _as_list(blocks, "Blok listesi")
    for block in block_list:
        _check_block(_as_dict(block, "Blok"), depth)
    return block_list


def _check_block(block: dict[str, Any], depth: int) -> None:
    if depth > MAX_BLOCK_DEPTH:
        raise _invalid(f"Bloklar en fazla {MAX_BLOCK_DEPTH} kat iç içe olabilir.")
    block_type = block.get("type")
    if block_type not in ALLOWED_BLOCK_TYPES:
        raise _invalid(f"İzin verilmeyen blok türü: {block_type}")
    props = _as_dict(block.get("props", {}), "Blok özellikleri")
    if block_type == "heading" and props.get("level") not in ALLOWED_HEADING_LEVELS:
        raise _invalid("Başlık seviyesi 1, 2 veya 3 olmalı.")
    for item in _as_list(block.get("content", []), "Blok içeriği"):
        _check_inline(_as_dict(item, "Satır içi öğe"))
    _check_blocks(block.get("children", []), depth + 1)


def _check_inline(item: dict[str, Any]) -> None:
    item_type = item.get("type")
    if item_type not in ALLOWED_INLINE_TYPES:
        raise _invalid(f"İzin verilmeyen satır içi tür: {item_type}")
    if item_type == "link":
        _check_link(item)
    if item_type == "pageMention":
        _as_dict(item.get("props", {}), "Sayfa bahsi özellikleri")


def _check_link(link: dict[str, Any]) -> None:
    scheme = urlsplit(str(link.get("href", ""))).scheme.lower()
    if scheme not in ALLOWED_LINK_SCHEMES:
        raise _invalid("Bağlantılar yalnızca http veya https olabilir.")
    for part in _as_list(link.get("content", []), "Bağlantı içeriği"):
        if _as_dict(part, "Bağlantı metni").get("type") != "text":
            raise _invalid("Bağlantının içinde yalnızca metin olabilir.")


def _plain_text(blocks: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for block in blocks:
        lines.append(_inline_text(block.get("content", [])))
        lines.append(_plain_text(block.get("children", [])))
    return "\n".join(line for line in lines if line)


def _inline_text(items: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for item in items:
        if item.get("type") == "text":
            parts.append(str(item.get("text", "")))
        elif item.get("type") == "link":
            parts.append(_inline_text(item.get("content", [])))
    return "".join(parts)


def _mentioned_page_ids(blocks: list[dict[str, Any]]) -> set[UUID]:
    ids: set[UUID] = set()
    for block in blocks:
        for item in block.get("content", []):
            if item.get("type") == "pageMention":
                ids.update(_parse_page_id(item.get("props", {}).get("pageId")))
        ids.update(_mentioned_page_ids(block.get("children", [])))
    return ids


def _parse_page_id(value: object) -> set[UUID]:
    try:
        return {UUID(str(value))}
    except ValueError:
        return set()  # Geçersiz kimlik yok sayılır (R-09).
