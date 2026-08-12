"""add uploader_status to users

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("uploader_status", sa.String(16), server_default="none", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "uploader_status")
