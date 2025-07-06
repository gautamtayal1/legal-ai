from models.document import Base
from core.database import engine
import time

def init_database():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise

if __name__ == "__main__":
    init_database() 