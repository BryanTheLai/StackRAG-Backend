import os
import asyncio
from fastapi import APIRouter, HTTPException, status
from supabase import create_client
from api.v1.dependencies import SUPABASE_URL, SUPABASE_KEY

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/live")
async def liveness_check():
    """Liveness probe: verifies that the FastAPI server process is running."""
    return {"status": "alive", "service": "StackRAG-Backend"}

@router.get("/ready")
async def readiness_check():
    """
    Readiness probe: verifies connectivity to Supabase database and storage dependencies
    within a strict 3.0 second deadline.
    """
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Check database connectivity with a timeout
        async def check_db():
            return supabase_client.table("processing_jobs").select("id").limit(1).execute()

        await asyncio.wait_for(check_db(), timeout=3.0)

        return {
            "status": "ready",
            "dependencies": {
                "supabase": "healthy",
                "database": "connected"
            }
        }
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_530_SITE_IS_FROZEN,
            detail="Readiness check timed out connecting to database."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Readiness check failed: {str(e)}"
        )
