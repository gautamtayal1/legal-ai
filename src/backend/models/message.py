from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, index=True)
    thread_id = Column(String, ForeignKey("threads.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    role = Column(
        Enum("user", "assistant", name="role_enum"),
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    thread = relationship("Thread", back_populates="messages")
    user = relationship("User", back_populates="messages")
    documents = relationship("Document", back_populates="messages", cascade="all, delete-orphan")