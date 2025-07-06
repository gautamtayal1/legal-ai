from sqlalchemy.ext.declarative import declarative_base

# Unified Base for all models
Base = declarative_base()

# Import all models
from .user import User
from .thread import Thread
from .message import Message
from .document import Document

# Make Base available to all models
User.metadata = Base.metadata
Thread.metadata = Base.metadata
Message.metadata = Base.metadata
Document.metadata = Base.metadata

__all__ = ["Base", "User", "Thread", "Message", "Document"] 