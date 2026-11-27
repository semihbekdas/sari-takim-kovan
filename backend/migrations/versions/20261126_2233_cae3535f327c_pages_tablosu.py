"""pages tablosu (#9; R-03, R-06, R-07, R-08, R-10, R-11)

Revision ID: cae3535f327c
Revises: 08ffb3ff6603
Create Date: 2026-11-26 22:33:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "cae3535f327c"
down_revision: str | Sequence[str] | None = "08ffb3ff6603"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column(
            "content",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("indexed_version", sa.Integer(), nullable=True),
        sa.Column("index_attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("index_error", sa.Text(), nullable=True),
        sa.Column("index_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], name=op.f("fk_pages_owner_id_users"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["pages.id"], name=op.f("fk_pages_parent_id_pages"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pages")),
    )
    op.create_index(
        "ix_pages_owner_parent",
        "pages",
        ["owner_id", "parent_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_pages_needs_index",
        "pages",
        ["updated_at"],
        postgresql_where=sa.text("indexed_version IS DISTINCT FROM version"),
    )


def downgrade() -> None:
    op.drop_index("ix_pages_needs_index", table_name="pages")
    op.drop_index("ix_pages_owner_parent", table_name="pages")
    op.drop_table("pages")
