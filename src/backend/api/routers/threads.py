from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form
from sqlalchemy.orm import Session
from core.database import get_db
from models.thread import Thread
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/threads",
    tags=["threads"],
)

@router.get("/")
async def list_threads(db: Session = Depends(get_db)):
    """Get all threads from the database."""
    threads = db.query(Thread).all()
    return [
        {
            "id": thread.id,
            "name": thread.name,
            "created_at": thread.created_at,
            "updated_at": thread.updated_at
        }
        for thread in threads
    ]

@router.post("/")
async def create_thread(threadId: str, userId: str, title: str, db: Session = Depends(get_db)):
    """Create a new thread."""
    thread = Thread(id=threadId, user_id=userId, title=title)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread

@router.get("/{threadId}")
async def get_thread(threadId: str, db: Session = Depends(get_db)):
    """Get a thread by its ID."""
    thread = db.query(Thread).filter(Thread.id == threadId).first()
    db.add(thread)
    db.commit()
    db.refresh(thread)
    