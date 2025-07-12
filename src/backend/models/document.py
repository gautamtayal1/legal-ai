from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from . import Base

class ProcessingStatus(PyEnum):
    PENDING = "pending"
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    PROCESSING = "processing"  
    CHUNKING = "chunking"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    document_url = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    thread_id = Column(String, ForeignKey("threads.id"), nullable=False)
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    error_message = Column(Text, nullable=True)
    
    user = relationship("User")
    thread = relationship("Thread", back_populates="documents")

