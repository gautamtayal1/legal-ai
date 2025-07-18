from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form, Query
from sqlalchemy.orm import Session
from core.database import get_db
from models.thread import Thread
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/threads",
    tags=["threads"],
)

class ThreadCreate(BaseModel):
    id: str
    user_id: str
    title: str

class ThreadUpdate(BaseModel):
    title: str

class ThreadAutoName(BaseModel):
    thread_id: str
    user_id: str

@router.get("")
async def list_threads(db: Session = Depends(get_db)):
    """Get all threads from the database."""
    threads = db.query(Thread).all()
    return [
        {
            "id": thread.id,
            "title": thread.title,
            "created_at": thread.created_at,
            "updated_at": thread.updated_at
        }
        for thread in threads
    ]

@router.post("")
async def create_thread(thread_data: ThreadCreate, db: Session = Depends(get_db)):
    """Create a new thread."""
    thread = Thread(
        id=thread_data.id, 
        user_id=thread_data.user_id, 
        title=thread_data.title
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread
    
@router.get("/{user_id}")
async def get_thread_by_user_id(user_id: str, db: Session = Depends(get_db)):
    """Get all threads for a specific user."""
    threads = db.query(Thread).filter(Thread.user_id == user_id).all()
    if not threads:
        raise HTTPException(status_code=404, detail="No threads found for this user")
    return threads