"""Initial migration

Revision ID: 878b16b63d78
Revises: 
Create Date: 2025-07-10 13:44:42.867210

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '878b16b63d78'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('documents', sa.Column('processing_status', sa.Enum('PENDING', 'PROCESSING', 'EXTRACTING', 'CHUNKING', 'EMBEDDING', 'READY', 'FAILED', name='processingstatus'), nullable=True))
    op.add_column('documents', sa.Column('error_message', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('documents', 'error_message')
    op.drop_column('documents', 'processing_status')
