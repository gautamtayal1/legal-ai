from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from models.message import Message
from models.thread import Thread
from pydantic import BaseModel
from typing import List
import uuid

router = APIRouter(
    prefix="/messages",
    tags=["messages"],
)

class MessageCreate(BaseModel):
    thread_id: str
    user_id: str
    content: str
    role: str = "user"

@router.post("/")
async def create_message(message_data: MessageCreate, db: Session = Depends(get_db)):
    thread = db.query(Thread).filter(
        Thread.id == message_data.thread_id,
        Thread.user_id == message_data.user_id
    ).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    message = Message(
        id=str(uuid.uuid4()),
        thread_id=message_data.thread_id,
        user_id=message_data.user_id,
        content=message_data.content,
        role=message_data.role
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return message

@router.get("/thread/{thread_id}")
async def get_messages(
    thread_id: str,
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    thread = db.query(Thread).filter(
        Thread.id == thread_id,
        Thread.user_id == user_id
    ).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    messages = db.query(Message).filter(
        Message.thread_id == thread_id
    ).order_by(Message.created_at.asc()).all()
    
    return messages
