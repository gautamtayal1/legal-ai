"""Add processing status

Revision ID: 84043afa3816
Revises: e9ff70812e0a
Create Date: 2025-07-11 16:35:01.162710

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '84043afa3816'
down_revision: Union[str, Sequence[str], None] = 'e9ff70812e0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    processing_status_enum = sa.Enum(
        'PENDING', 'EXTRACTING', 'PROCESSING', 'CHUNKING', 
        'EMBEDDING', 'READY', 'FAILED', 
        name='processingstatus'
    )
    processing_status_enum.create(op.get_bind())


def downgrade() -> None:
    """Downgrade schema."""
    op.execute('DROP TYPE IF EXISTS processingstatus')
