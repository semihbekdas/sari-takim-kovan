"""Veritabanı tabloları (SQLAlchemy Core, ADR-003).

Tablolar bu `metadata`'ya eklenir; Alembic `--autogenerate` farkları buradan bulur.
Şema taslağı: docs/domain-design.md § 9.
"""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

# Kısıt ve indeks adları sabit bir kurala göre üretilir. Böylece migration'lar her bilgisayarda
# aynı adları üretir ve sonradan bir kısıtı adıyla silmek mümkün olur.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)

users = Table(
    "users",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("email", Text, nullable=False),
    Column("display_name", Text, nullable=False),
    Column("password_hash", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

# R-01: E-posta büyük/küçük harf duyarsız benzersizdir ("Ayse@x.com" ile "ayse@x.com" aynı hesap).
Index("ux_users_email", func.lower(users.c.email), unique=True)

pages = Table(
    "pages",
    metadata,
    Column("id", Uuid, primary_key=True),
    # Kullanıcı silinirse sayfaları da silinir; üst sayfa silinirse alt sayfalar da silinir.
    Column("owner_id", Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("parent_id", Uuid, ForeignKey("pages.id", ondelete="CASCADE"), nullable=True),
    Column("title", String(200), nullable=False),  # R-03
    Column("content", JSONB, nullable=False, server_default=text("'[]'::jsonb")),  # R-06
    Column("version", Integer, nullable=False, server_default=text("1")),  # R-07
    Column("deleted_at", DateTime(timezone=True), nullable=True),  # R-08
    # İndeksleme durumu (R-10, R-11; ADR-005)
    Column("indexed_version", Integer, nullable=True),
    Column("index_attempts", Integer, nullable=False, server_default=text("0")),
    Column("index_error", Text, nullable=True),
    Column("index_retry_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

# Sol menü ağacı: Bir kullanıcının silinmemiş sayfaları, üst sayfaya göre.
Index(
    "ix_pages_owner_parent",
    pages.c.owner_id,
    pages.c.parent_id,
    postgresql_where=pages.c.deleted_at.is_(None),
)
# İndeksleme döngüsü: İndekslenmeyi bekleyen sayfalar (ADR-005).
Index(
    "ix_pages_needs_index",
    pages.c.updated_at,
    postgresql_where=pages.c.indexed_version.is_distinct_from(pages.c.version),
)
