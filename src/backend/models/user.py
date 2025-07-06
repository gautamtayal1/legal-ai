from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    threads = relationship("Thread", back_populates="user")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")