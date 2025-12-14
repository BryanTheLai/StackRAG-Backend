from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks
from typing import Dict, Any, Optional
import uuid
import io
import os
import re
import asyncio
import random
import logging

from ..dependencies import Session, get_session, SUPABASE_URL, SUPABASE_KEY
from supabase import create_client
from src.pipeline import IngestionPipeline
from src.storage.SupabaseService import SupabaseService

router = APIRouter(prefix="/documents", tags=["documents"])

logger = logging.getLogger("uvicorn.error")


# Throttle concurrent ingestion jobs (helps avoid Gemini quota/rate bursts)
_MAX_CONCURRENT_INGESTIONS = int(os.getenv("MAX_CONCURRENT_INGESTIONS", "2"))
_INGESTION_SEMAPHORE = asyncio.Semaphore(_MAX_CONCURRENT_INGESTIONS)


def _parse_retry_after_seconds(error_text: str) -> Optional[float]:
    """Best-effort extraction of server-provided retry delays from Gemini errors."""
    if not error_text:
        return None

    # Examples we may see:
    # - "Please retry in 41.466s."
    # - "'retryDelay': '41s'"
    m = re.search(r"retry in\s+(\d+(?:\.\d+)?)s", error_text, flags=re.IGNORECASE)
    if m:
        return float(m.group(1))
    m = re.search(r"retryDelay\s*['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s", error_text, flags=re.IGNORECASE)
    if m:
        return float(m.group(1))
    return None


def _get_user_friendly_error(exception_str: str) -> tuple[str, str]:
    """
    Convert technical errors to user-friendly messages.
    Returns: (user_message, error_code)
    """
    error_lower = exception_str.lower()
    
    # API Key errors
    if "401" in exception_str or "invalid_api_key" in error_lower or "incorrect api key" in error_lower:
        return ("AI service temporarily unavailable. Please try again later or contact support.", "api_key_invalid")
    
    # Rate limit / quota exhaustion
    if "429" in exception_str or "rate_limit" in error_lower or "resource_exhausted" in error_lower or "quota" in error_lower:
        # Gemini free-tier commonly returns RESOURCE_EXHAUSTED. Make this explicit.
        if "resource_exhausted" in error_lower or "quota" in error_lower:
            return (
                "Upload rate limit reached while processing this PDF. Please wait a bit and retry, or upload fewer files at once.",
                "quota_exhausted",
            )
        return ("Service is busy. Please wait a moment and try again.", "rate_limit")
    
    # File parsing errors
    if "parsing" in error_lower or "pdf" in error_lower and "corrupt" in error_lower:
        return ("Unable to read PDF file. The file may be corrupted or password-protected.", "file_corrupted")
    
    # Embedding errors
    if "embedding" in error_lower:
        return ("Failed to process document content. Please try again.", "embedding_failed")
    
    # Network errors
    if "connection" in error_lower or "timeout" in error_lower:
        return ("Network connection issue. Please check your connection and retry.", "network_error")
    
    # Database errors
    if "supabase" in error_lower or "database" in error_lower:
        return ("Database error. Please try again or contact support.", "database_error")
    
    # Generic fallback
    return ("An unexpected error occurred. Please try again.", "unknown_error")


async def _process_document_background(
    job_id: uuid.UUID,
    pdf_bytes: bytes,
    user_id: uuid.UUID,
    filename: str,
    doc_type: str,
    token: str
):
    """Background task to process document and update job status."""
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase_client.options.headers["Authorization"] = f"Bearer {token}"
    acquired = False
    
    try:
        await _INGESTION_SEMAPHORE.acquire()
        acquired = True

        logger.info(
            "processing_job_start job_id=%s filename=%s max_concurrent=%s",
            str(job_id),
            filename,
            _MAX_CONCURRENT_INGESTIONS,
        )

        # Update to parsing status
        supabase_client.table("processing_jobs").update({
            "status": "parsing",
            "current_step": "Reading PDF...",
            "progress_percentage": 10
        }).eq("id", str(job_id)).execute()
        
        # Create file buffer from bytes
        file_buffer = io.BytesIO(pdf_bytes)
        
        # Initialize services
        supabase_service = SupabaseService(supabase_client)
        pipeline = IngestionPipeline(supabase_service=supabase_service)
        
        # Run pipeline with limited retries for transient quota bursts.
        max_attempts = int(os.getenv("DOCUMENT_PROCESS_MAX_ATTEMPTS", "3"))
        last_result: Optional[Dict[str, Any]] = None
        last_error: Optional[Exception] = None

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(
                    "processing_job_attempt job_id=%s filename=%s attempt=%s/%s",
                    str(job_id),
                    filename,
                    attempt,
                    max_attempts,
                )
                last_result = await pipeline.run(
                    pdf_file_buffer=file_buffer,
                    user_id=user_id,
                    original_filename=filename,
                    doc_type=doc_type,
                    job_id=job_id  # Pass job_id for progress updates
                )

                # If the pipeline itself reports a failure, decide if it's retryable.
                if last_result.get("success"):
                    break

                msg = str(last_result.get("message", ""))
                is_retryable = ("429" in msg) or ("resource_exhausted" in msg.lower()) or ("rate limit" in msg.lower())
                if not is_retryable or attempt >= max_attempts:
                    break

                retry_after = _parse_retry_after_seconds(msg)
                sleep_s = retry_after if retry_after is not None else min(2 ** attempt, 30)
                sleep_s += random.uniform(0, 0.5)
                supabase_client.table("processing_jobs").update({
                    "status": "parsing",
                    "current_step": f"Rate limited. Retrying (attempt {attempt + 1}/{max_attempts})...",
                    "progress_percentage": 10
                }).eq("id", str(job_id)).execute()
                await asyncio.sleep(sleep_s)
                file_buffer.seek(0)

            except Exception as e:
                last_error = e
                msg = str(e)
                is_retryable = ("429" in msg) or ("resource_exhausted" in msg.lower()) or ("rate limit" in msg.lower())
                if not is_retryable or attempt >= max_attempts:
                    break
                retry_after = _parse_retry_after_seconds(msg)
                sleep_s = retry_after if retry_after is not None else min(2 ** attempt, 30)
                sleep_s += random.uniform(0, 0.5)
                logger.warning(
                    "processing_job_retry job_id=%s filename=%s sleep_s=%.2f reason=%s",
                    str(job_id),
                    filename,
                    sleep_s,
                    ("quota" if "resource_exhausted" in msg.lower() else "rate_limit"),
                )
                await asyncio.sleep(sleep_s)
                file_buffer.seek(0)

        if last_result is None and last_error is not None:
            raise last_error

        result = last_result or {"success": False, "message": "Unknown processing error"}
        
        if result.get("success"):
            logger.info(
                "processing_job_success job_id=%s filename=%s document_id=%s",
                str(job_id),
                filename,
                str(result.get("document_id")) if result.get("document_id") else None,
            )
            # Convert UUID to string for JSON serialization
            result_data = {
                "success": result.get("success"),
                "message": result.get("message"),
                "document_id": str(result.get("document_id")) if result.get("document_id") else None,
                "chunk_count": result.get("chunk_count")
            }
            
            # Mark as completed
            supabase_client.table("processing_jobs").update({
                "status": "completed",
                "current_step": "Complete!",
                "progress_percentage": 100,
                "document_id": str(result.get("document_id")) if result.get("document_id") else None,
                "result_data": result_data,
                "completed_at": "now()"
            }).eq("id", str(job_id)).execute()
        else:
            # Mark as failed with user-friendly error
            user_error, error_code = _get_user_friendly_error(result.get("message", ""))
            logger.error(
                "processing_job_failed job_id=%s filename=%s error_code=%s",
                str(job_id),
                filename,
                error_code,
            )
            supabase_client.table("processing_jobs").update({
                "status": "failed",
                "error_message": user_error,
                "error_code": error_code,
                "completed_at": "now()"
            }).eq("id", str(job_id)).execute()
            
    except Exception as e:
        # Mark as failed on exception with user-friendly error
        error_str = str(e)
        user_error, error_code = _get_user_friendly_error(error_str)
        
        logger.exception(
            "processing_job_exception job_id=%s filename=%s",
            str(job_id),
            filename,
        )
        
        try:
            supabase_client.table("processing_jobs").update({
                "status": "failed",
                "error_message": user_error,
                "error_code": error_code,
                "completed_at": "now()"
            }).eq("id", str(job_id)).execute()
        except:
            pass  # If we can't even update the status, log it
            print(f"[ERROR] Failed to update job status for {job_id}")
    finally:
        if acquired:
            try:
                _INGESTION_SEMAPHORE.release()
            except Exception:
                pass


@router.post("/process", response_model=Dict[str, Any])
async def process_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Upload and queue a document for processing.
    Returns immediately with a job_id for status tracking.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF files are supported."
        )
    
    if file.content_type and file.content_type != 'application/pdf':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. PDF required."
        )
    
    # Validate file size (50MB limit)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 50MB."
        )
    
    # Reset file pointer after reading
    await file.seek(0)
    
    # Initialize Supabase client
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase_client.options.headers["Authorization"] = f"Bearer {session.token}"
    
    try:
        # Create processing job record
        job_id = uuid.uuid4()
        logger.info(
            "process_document_received job_id=%s filename=%s size_bytes=%s",
            str(job_id),
            file.filename,
            len(file_content),
        )
        job_data = {
            "id": str(job_id),
            "user_id": session.user_id,
            "filename": file.filename,
            "status": "pending",
            "current_step": "Queued for processing...",
            "progress_percentage": 0
        }
        
        response = supabase_client.table("processing_jobs").insert(job_data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create processing job"
            )
        
        # Queue background processing
        background_tasks.add_task(
            _process_document_background,
            job_id=job_id,
            pdf_bytes=file_content,
            user_id=uuid.UUID(session.user_id),
            filename=file.filename,
            doc_type=file.filename.split('.')[-1],
            token=session.token
        )
        
        return {
            "success": True,
            "message": "Document queued for processing",
            "job_id": str(job_id),
            "filename": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue document: {str(e)}"
        )


@router.get("/processing-status/{job_id}", response_model=Dict[str, Any])
async def get_processing_status(
    job_id: str,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get the current status of a document processing job.
    Used by frontend to poll progress after upload.
    """
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase_client.options.headers["Authorization"] = f"Bearer {session.token}"
    
    try:
        response = supabase_client.table("processing_jobs")\
            .select("*")\
            .eq("id", job_id)\
            .eq("user_id", session.user_id)\
            .single()\
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Processing job not found"
            )
        
        return response.data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch processing status: {str(e)}"
        )


@router.post("/retry/{job_id}", response_model=Dict[str, Any])
async def retry_failed_job(
    background_tasks: BackgroundTasks,
    job_id: str,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Retry a failed processing job.
    Fetches the original file from storage and re-processes it.
    """
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase_client.options.headers["Authorization"] = f"Bearer {session.token}"
    
    try:
        # Get the failed job
        job_response = supabase_client.table("processing_jobs")\
            .select("*")\
            .eq("id", job_id)\
            .eq("user_id", session.user_id)\
            .single()\
            .execute()
        
        if not job_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Processing job not found"
            )
        
        job_data = job_response.data
        
        # Check if job can be retried (must be failed)
        if job_data["status"] not in ["failed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot retry job with status: {job_data['status']}"
            )
        
        # If document_id exists, get the file from storage
        if job_data.get("document_id"):
            doc_response = supabase_client.table("documents")\
                .select("storage_path")\
                .eq("id", job_data["document_id"])\
                .single()\
                .execute()
            
            if doc_response.data and doc_response.data.get("storage_path"):
                # Download file from storage
                storage_path = doc_response.data["storage_path"]
                file_data = supabase_client.storage.from_("financial-pdfs").download(storage_path)
                pdf_bytes = file_data
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Original file not found in storage. Please re-upload."
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot retry - original file not found. Please re-upload."
            )
        
        # Reset job status for retry
        retry_count = job_data.get("retry_count", 0) + 1
        supabase_client.table("processing_jobs").update({
            "status": "pending",
            "current_step": "Retrying...",
            "progress_percentage": 0,
            "retry_count": retry_count,
            "error_message": None,
            "error_code": None,
            "updated_at": "now()"
        }).eq("id", job_id).execute()
        
        # Queue for reprocessing
        background_tasks.add_task(
            _process_document_background,
            job_id=uuid.UUID(job_id),
            pdf_bytes=pdf_bytes,
            user_id=uuid.UUID(session.user_id),
            filename=job_data["filename"],
            doc_type=job_data["filename"].split('.')[-1],
            token=session.token
        )
        
        return {
            "success": True,
            "message": "Job queued for retry",
            "job_id": job_id,
            "retry_count": retry_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry job: {str(e)}"
        )