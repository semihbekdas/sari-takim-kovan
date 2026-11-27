"""Sayfayı arama parçalarına bölen saf fonksiyon (ADR-009)."""

from dataclasses import dataclass

from kovan.domain.content import PageContent

DEFAULT_CHUNK_MAX_CHARS = 1000
HEADING_SEPARATOR = " › "
BLOCK_SEPARATOR = "\n"


@dataclass(frozen=True)
class Chunk:
    """Bir arama parçası. `text` ham metindir; başlık öneki indekslemede eklenir (#15)."""

    heading_path: str
    text: str


def chunk_page(
    title: str, content: PageContent, max_chars: int = DEFAULT_CHUNK_MAX_CHARS
) -> list[Chunk]:
    """Sayfayı başlık bölümlerine, bölümleri en fazla `max_chars` karakterlik parçalara böler."""
    if max_chars < 1:
        raise ValueError("max_chars en az 1 olmalı.")
    chunks: list[Chunk] = []
    for section in content.to_sections():
        path = HEADING_SEPARATOR.join((title, *section.headings))
        for text in _pack(section.texts, max_chars):
            chunks.append(Chunk(heading_path=path, text=text))
    return chunks


def _pack(texts: tuple[str, ...], max_chars: int) -> list[str]:
    """Blokları sırayla parçalara doldurur; sınırı tek başına aşan blok sabit uzunlukta bölünür."""
    parts: list[str] = []
    current = ""
    for text in texts:
        for piece in _split_long(text, max_chars):
            joined = f"{current}{BLOCK_SEPARATOR}{piece}" if current else piece
            if len(joined) <= max_chars:
                current = joined
                continue
            parts.append(current)
            current = piece
    if current:
        parts.append(current)
    return parts


def _split_long(text: str, max_chars: int) -> list[str]:
    return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]
