from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# PostgreSQL database URL - using Docker container configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://inquire_user:inquire_pass@127.0.0.1:5432/inquire_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 