"""Add user preferences

Revision ID: 6b6f789a0583
Revises: 976f984cc9a4
Create Date: 2025-07-10 14:17:50.114613

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6b6f789a0583'
down_revision: Union[str, Sequence[str], None] = '976f984cc9a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
