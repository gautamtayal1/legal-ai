"""sync_processing_status_with_model

Revision ID: 001fc46d5e98
Revises: 1cfb593ad987
Create Date: 2025-07-12 12:35:41.706160

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '001fc46d5e98'
down_revision: Union[str, Sequence[str], None] = '1cfb593ad987'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Update ProcessingStatus enum to match current model
    # Current model has: PENDING, UPLOADED, EXTRACTING, PROCESSING, CHUNKING, INDEXING, READY, FAILED
    
    # Get connection to check existing enum values
    conn = op.get_bind()
    
    # Check existing enum values
    result = conn.execute(
        text("SELECT unnest(enum_range(NULL::processingstatus))")
    ).fetchall()
    existing_values = [row[0] for row in result]
    
    # Add new values that are in the model but not in the database
    values_to_add = [
        ('uploaded', 'pending'),
        ('extracting', 'uploaded'),
        ('processing', 'extracting'),
        ('chunking', 'processing')
    ]
    
    for value, after_value in values_to_add:
        if value not in existing_values:
            try:
                if after_value in existing_values:
                    conn.execute(text(f"ALTER TYPE processingstatus ADD VALUE '{value}' AFTER '{after_value}'"))
                else:
                    conn.execute(text(f"ALTER TYPE processingstatus ADD VALUE '{value}'"))
            except Exception as e:
                # If there's still an error, continue with the next value
                print(f"Warning: Could not add enum value '{value}': {e}")


def downgrade() -> None:
    """Downgrade schema."""
    # Note: PostgreSQL doesn't support removing enum values easily
    # You would need to recreate the enum type to remove values
    # For now, we'll leave this as a no-op since removing enum values
    # is complex and rarely needed in development
    pass
