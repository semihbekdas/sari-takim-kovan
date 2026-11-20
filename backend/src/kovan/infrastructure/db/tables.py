"""Veritabanı tabloları (SQLAlchemy Core, ADR-003).

Tablolar bu `metadata`'ya eklenir; Alembic `--autogenerate` farkları buradan bulur.
İlk tablo (`pages`) #9'da eklenecek.
"""

from sqlalchemy import MetaData

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
