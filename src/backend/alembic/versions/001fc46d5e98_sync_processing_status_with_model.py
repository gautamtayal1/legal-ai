"""sync_processing_status_with_model

Revision ID: 001fc46d5e98
Revises: 1cfb593ad987
Create Date: 2025-07-12 12:35:41.706160

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = '001fc46d5e98'
down_revision: Union[str, Sequence[str], None] = '1cfb593ad987'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    conn = op.get_bind()
    
    result = conn.execute(
        text("SELECT unnest(enum_range(NULL::processingstatus))")
    ).fetchall()
    existing_values = [row[0] for row in result]
    
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
                print(f"Warning: Could not add enum value '{value}': {e}")


def downgrade() -> None:
    """Downgrade schema."""
    pass
