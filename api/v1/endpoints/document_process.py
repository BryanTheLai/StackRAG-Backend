from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from typing import Dict, Any
import uuid

from ..dependencies import Session, get_session, SUPABASE_URL, SUPABASE_KEY
from supabase import create_client
from src.pipeline import IngestionPipeline
from src.storage.SupabaseService import SupabaseService

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/process", response_model=Dict[str, Any])
async def process_document(
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Authenticate user, accept a PDF file, and process it through the ingestion pipeline."""
    # Validate file type
    if file.content_type != 'application/pdf':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. PDF required."
        )

    # Initialize Supabase client with user token for secure operations
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase_client.options.headers["Authorization"] = f"Bearer {session.token}"
    supabase_service = SupabaseService(supabase_client)

    # Initialize ingestion pipeline with provided SupabaseService
    pipeline = IngestionPipeline(supabase_service=supabase_service)

    try:
        # Run the pipeline
        result = await pipeline.run(
            pdf_file_buffer=file.file,
            user_id=uuid.UUID(session.user_id),
            original_filename=file.filename,
            doc_type=file.filename.split('.')[-1]
        )
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {e}"
        )