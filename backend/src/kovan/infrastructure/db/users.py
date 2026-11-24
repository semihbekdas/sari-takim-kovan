"""`UserRepository` port'unun PostgreSQL uygulaması (SQLAlchemy Core)."""

from uuid import UUID

from sqlalchemy import Engine, insert
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
