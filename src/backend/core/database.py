from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# PostgreSQL database URL - using default postgres user for initial setup
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:@localhost:5432/postgres"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 