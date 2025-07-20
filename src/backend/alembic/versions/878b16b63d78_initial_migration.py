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
    
    # Drop existing enums and tables if they exist
    op.execute("DROP TABLE IF EXISTS documents CASCADE")
    op.execute("DROP TABLE IF EXISTS messages CASCADE") 
    op.execute("DROP TABLE IF EXISTS threads CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP TYPE IF EXISTS role_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS processingstatus CASCADE")
    
    # Create enums
    op.execute("CREATE TYPE role_enum AS ENUM ('user', 'assistant')")
    op.execute("CREATE TYPE processingstatus AS ENUM ('pending', 'uploaded', 'extracting', 'processing', 'chunking', 'indexing', 'ready', 'failed')")
    
    # Create tables using raw SQL
    op.execute("""
        CREATE TABLE users (
            id VARCHAR NOT NULL,
            email VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            avatar_url VARCHAR,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (id)
        )
    """)
    
    op.execute("CREATE UNIQUE INDEX ix_users_email ON users (email)")
    op.execute("CREATE INDEX ix_users_id ON users (id)")
    
    op.execute("""
        CREATE TABLE threads (
            id VARCHAR NOT NULL,
            user_id VARCHAR NOT NULL,
            title VARCHAR NOT NULL,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (id),
            FOREIGN KEY(user_id) REFERENCES users (id)
        )
    """)
    
    op.execute("CREATE INDEX ix_threads_id ON threads (id)")
    
    op.execute("""
        CREATE TABLE messages (
            id VARCHAR NOT NULL,
            thread_id VARCHAR NOT NULL,
            user_id VARCHAR NOT NULL,
            content TEXT NOT NULL,
            role role_enum NOT NULL,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (id),
            FOREIGN KEY(thread_id) REFERENCES threads (id),
            FOREIGN KEY(user_id) REFERENCES users (id)
        )
    """)
    
    op.execute("CREATE INDEX ix_messages_id ON messages (id)")
    
    op.execute("""
        CREATE TABLE documents (
            id SERIAL NOT NULL,
            document_url VARCHAR NOT NULL,
            filename VARCHAR NOT NULL,
            file_type VARCHAR NOT NULL,
            file_size INTEGER NOT NULL,
            user_id VARCHAR NOT NULL,
            uploaded_at TIMESTAMP,
            thread_id VARCHAR NOT NULL,
            processing_status processingstatus,
            error_message TEXT,
            PRIMARY KEY (id),
            FOREIGN KEY(thread_id) REFERENCES threads (id),
            FOREIGN KEY(user_id) REFERENCES users (id)
        )
    """)
    
    op.execute("CREATE INDEX ix_documents_id ON documents (id)")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE IF EXISTS documents CASCADE")
    op.execute("DROP TABLE IF EXISTS messages CASCADE")
    op.execute("DROP TABLE IF EXISTS threads CASCADE") 
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP TYPE IF EXISTS role_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS processingstatus CASCADE")