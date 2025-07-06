from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

@router.get("/")
async def list_documents():
    """Placeholder endpoint returning no documents yet."""
    return []

@router.get("/{doc_id}")
async def get_document(doc_id: str):
    """Fetch single document placeholder"""
    raise HTTPException(status_code=404, detail="Document not found")
