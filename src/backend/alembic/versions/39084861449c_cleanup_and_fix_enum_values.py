"""cleanup_and_fix_enum_values

Revision ID: 39084861449c
Revises: ce5151184049
Create Date: 2025-07-12 12:55:12.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = '39084861449c'
down_revision: Union[str, Sequence[str], None] = 'ce5151184049'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    conn = op.get_bind()
    
    conn.execute(text("""
        CREATE TYPE processingstatus_new AS ENUM (
            'pending',
            'uploaded', 
            'extracting',
            'processing',
            'chunking',
            'indexing',
            'ready',
            'failed'
        )
    """))
    
    conn.execute(text("""
        ALTER TABLE documents 
        ALTER COLUMN processing_status TYPE processingstatus_new 
        USING (
            CASE 
                WHEN processing_status::text = 'PENDING' THEN 'pending'::processingstatus_new
                WHEN processing_status::text = 'UPLOADING' THEN 'uploaded'::processingstatus_new
                WHEN processing_status::text = 'EXTRACTING' THEN 'extracting'::processingstatus_new
                WHEN processing_status::text = 'PROCESSING' THEN 'processing'::processingstatus_new
                WHEN processing_status::text = 'CHUNKING' THEN 'chunking'::processingstatus_new
                WHEN processing_status::text = 'EMBEDDING' THEN 'processing'::processingstatus_new
                WHEN processing_status::text = 'STORING' THEN 'processing'::processingstatus_new
                WHEN processing_status::text = 'INDEXING' THEN 'indexing'::processingstatus_new
                WHEN processing_status::text = 'READY' THEN 'ready'::processingstatus_new
                WHEN processing_status::text = 'FAILED' THEN 'failed'::processingstatus_new
                WHEN processing_status::text = 'pending' THEN 'pending'::processingstatus_new
                WHEN processing_status::text = 'uploaded' THEN 'uploaded'::processingstatus_new
                WHEN processing_status::text = 'extracting' THEN 'extracting'::processingstatus_new
                WHEN processing_status::text = 'processing' THEN 'processing'::processingstatus_new
                WHEN processing_status::text = 'chunking' THEN 'chunking'::processingstatus_new
                WHEN processing_status::text = 'indexing' THEN 'indexing'::processingstatus_new
                WHEN processing_status::text = 'ready' THEN 'ready'::processingstatus_new
                WHEN processing_status::text = 'failed' THEN 'failed'::processingstatus_new
                ELSE 'pending'::processingstatus_new
            END
        )
    """))
    
    conn.execute(text("DROP TYPE processingstatus"))
    
    conn.execute(text("ALTER TYPE processingstatus_new RENAME TO processingstatus"))


def downgrade() -> None:
    """Downgrade schema."""
    pass
