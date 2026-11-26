"""Veritabanı tabloları (SQLAlchemy Core, ADR-003).

Tablolar bu `metadata`'ya eklenir; Alembic `--autogenerate` farkları buradan bulur.
Şema taslağı: docs/domain-design.md § 9.
"""

from sqlalchemy import Column, DateTime, Index, MetaData, Table, Text, Uuid, func

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
