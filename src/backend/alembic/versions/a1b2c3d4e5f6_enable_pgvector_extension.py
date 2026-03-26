"""Enable pgvector extension

Revision ID: a1b2c3d4e5f6
Revises: 878b16b63d78
Create Date: 2026-03-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '878b16b63d78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable the pgvector extension for vector similarity search."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Drop the pgvector extension."""
    op.execute("DROP EXTENSION IF EXISTS vector")
