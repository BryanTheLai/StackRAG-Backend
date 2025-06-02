from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from supabase import create_client

from ..dependencies import Session, get_session, SUPABASE_URL, SUPABASE_KEY


class Document(BaseModel):
    id: str
    filename: str
    user_id: str


router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/", response_model=List[Document])
async def list_documents(session: Session = Depends(get_session)) -> List[Document]:
    """Get all documents for the authenticated user."""
    # Create ad-hoc Supabase client for this request only
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    client.options.headers["Authorization"] = f"Bearer {session.token}"
    
    response = (
        client.table("documents")
        .select("id, filename, user_id")
        .eq("user_id", session.user_id)
        .execute()
    )
    
    return [Document(**item) for item in response.data or []]
