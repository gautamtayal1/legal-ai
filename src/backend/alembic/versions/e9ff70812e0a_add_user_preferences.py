"""Add user preferences

Revision ID: e9ff70812e0a
Revises: 6b6f789a0583
Create Date: 2025-07-10 14:18:20.952401

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e9ff70812e0a'
down_revision: Union[str, Sequence[str], None] = '6b6f789a0583'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('documents', 'processing_progress')
    op.drop_column('documents', 'processing_step')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('documents', sa.Column('processing_step', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('documents', sa.Column('processing_progress', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=True))
