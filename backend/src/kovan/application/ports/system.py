"""Sistem seviyesindeki port'lar."""

from typing import Protocol


class ReadinessProbe(Protocol):
    """Bir bağımlılığın (veritabanı, Qdrant vb.) hazır olup olmadığını söyler.

    Uygulamalar asla exception fırlatmaz: Bağımlılığa ulaşılamıyorsa `False` döner.
    """

    @property
    def name(self) -> str: ...

    def is_ready(self) -> bool: ...
