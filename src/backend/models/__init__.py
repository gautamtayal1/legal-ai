from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from .user import User
from .thread import Thread
from .message import Message
from .document import Document

User.metadata = Base.metadata
Thread.metadata = Base.metadata
Message.metadata = Base.metadata
Document.metadata = Base.metadata

__all__ = ["Base", "User", "Thread", "Message", "Document"] 