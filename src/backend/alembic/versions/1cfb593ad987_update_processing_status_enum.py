"""update_processing_status_enum

Revision ID: 1cfb593ad987
Revises: 84043afa3816
Create Date: 2025-07-11 16:36:47.669215

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1cfb593ad987'
down_revision: Union[str, Sequence[str], None] = '84043afa3816'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add missing enum values to ProcessingStatus
    # PostgreSQL requires specific syntax for adding enum values
    
    # Add UPLOADING after PENDING
    op.execute("ALTER TYPE processingstatus ADD VALUE 'UPLOADING' AFTER 'PENDING'")
    
    # Add STORING after EMBEDDING  
    op.execute("ALTER TYPE processingstatus ADD VALUE 'STORING' AFTER 'EMBEDDING'")
    
    # Add INDEXING after STORING
    op.execute("ALTER TYPE processingstatus ADD VALUE 'INDEXING' AFTER 'STORING'")


def downgrade() -> None:
    """Downgrade schema."""
    # Note: PostgreSQL doesn't support removing enum values easily
    # You would need to recreate the enum type to remove values
    # For now, we'll leave this as a no-op since removing enum values
    # is complex and rarely needed in development
    pass
