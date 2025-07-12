"""fix_processing_status_enum_values

Revision ID: ce5151184049
Revises: 001fc46d5e98
Create Date: 2025-07-12 12:47:50.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'ce5151184049'
down_revision: Union[str, Sequence[str], None] = '001fc46d5e98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add the missing lowercase enum values that the Python model expects
    # Model expects: pending, uploaded, extracting, processing, chunking, indexing, ready, failed
    
    conn = op.get_bind()
    
    # Get current enum values
    result = conn.execute(
        text("SELECT unnest(enum_range(NULL::processingstatus))")
    ).fetchall()
    existing_values = [row[0] for row in result]
    
    # Add missing lowercase values
    missing_values = [
        'pending',
        'indexing', 
        'ready',
        'failed'
    ]
    
    for value in missing_values:
        if value not in existing_values:
            try:
                conn.execute(text(f"ALTER TYPE processingstatus ADD VALUE '{value}'"))
                print(f"Added enum value: {value}")
            except Exception as e:
                print(f"Warning: Could not add enum value '{value}': {e}")


def downgrade() -> None:
    """Downgrade schema."""
    # PostgreSQL doesn't support removing enum values easily
    # This is a no-op for safety
    pass
