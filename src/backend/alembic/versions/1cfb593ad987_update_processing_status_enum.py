"""update_processing_status_enum

Revision ID: 1cfb593ad987
Revises: 84043afa3816
Create Date: 2025-07-11 16:36:47.669215

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1cfb593ad987'
down_revision: Union[str, Sequence[str], None] = '84043afa3816'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    op.execute("ALTER TYPE processingstatus ADD VALUE 'UPLOADING' AFTER 'PENDING'")
    
    op.execute("ALTER TYPE processingstatus ADD VALUE 'STORING' AFTER 'EMBEDDING'")
    
    op.execute("ALTER TYPE processingstatus ADD VALUE 'INDEXING' AFTER 'STORING'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
