"""Testlerde kullanılan fake port uygulamaları ve sabitler."""

from dataclasses import dataclass

# Bağlanılamayan bir adres: Testler gerçek veritabanına ihtiyaç duymaz.
UNREACHABLE_DATABASE_URL = "postgresql+psycopg://kovan:kovan@127.0.0.1:1/kovan"


@dataclass
class FakeProbe:
    """`ReadinessProbe` port'unun test karşılığı."""

    name: str
    ready: bool

    def is_ready(self) -> bool:
        return self.ready
