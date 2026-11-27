"""`UserRepository` port'unun PostgreSQL uygulaması (SQLAlchemy Core)."""

from uuid import UUID

from sqlalchemy import ColumnElement, Engine, insert, select
from sqlalchemy.exc import IntegrityError

from kovan.domain.errors import ConflictError
from kovan.domain.users import User
from kovan.infrastructure.db.tables import users

EMAIL_INDEX_NAME = "ux_users_email"


class SqlUserRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, *, user_id: UUID, email: str, display_name: str, password_hash: str) -> User:
        statement = (
            insert(users)
            .values(id=user_id, email=email, display_name=display_name, password_hash=password_hash)
            .returning(users.c.created_at)
        )
        try:
            with self._engine.begin() as connection:
                created_at = connection.execute(statement).scalar_one()
        except IntegrityError as error:
            if EMAIL_INDEX_NAME not in str(error.orig):
                raise
            raise ConflictError("Bu e-posta zaten kayıtlı.", code="EMAIL_TAKEN") from error
        return User(user_id, email, display_name, password_hash, created_at)

    def get_by_email(self, email: str) -> User | None:
        return self._find_one(users.c.email == email)

    def get_by_id(self, user_id: UUID) -> User | None:
        return self._find_one(users.c.id == user_id)

    def _find_one(self, condition: ColumnElement[bool]) -> User | None:
        statement = select(
            users.c.id,
            users.c.email,
            users.c.display_name,
            users.c.password_hash,
            users.c.created_at,
        ).where(condition)
        with self._engine.connect() as connection:
            row = connection.execute(statement).one_or_none()
        if row is None:
            return None
        return User(row.id, row.email, row.display_name, row.password_hash, row.created_at)
