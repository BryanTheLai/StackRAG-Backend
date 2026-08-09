import os
import time
import uuid
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from supabase import create_client
from api.v1.dependencies import SUPABASE_URL, SUPABASE_KEY
from src.pipeline import IngestionPipeline
from src.storage.SupabaseService import SupabaseService

logger = logging.getLogger("uvicorn.error")

WORKER_ID = f"worker-{os.getpid()}-{uuid.uuid4().hex[:6]}"
LEASE_DURATION_SECONDS = 300  # 5 minutes
HEARTBEAT_INTERVAL_SECONDS = 15

class IngestionWorker:
    """
    Durable database-backed queue worker for document ingestion jobs.
    Acquires jobs atomically using lease locks, updates heartbeats, and reclaims stale leases.
    """

    def __init__(self):
        self.supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.supabase_service = SupabaseService(self.supabase_client)
        self.pipeline = IngestionPipeline(supabase_service=self.supabase_service)
        self.running = False

    async def acquire_job(self) -> Optional[Dict[str, Any]]:
        """
        Acquire a pending job or reclaim a stale leased job atomically.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        lease_until_iso = (datetime.now(timezone.utc) + timedelta(seconds=LEASE_DURATION_SECONDS)).isoformat()

        try:
            # Query for eligible jobs: pending or stale lease
            res = (
                self.supabase_client.table("processing_jobs")
                .select("*")
                .or_(f"status.eq.pending,and(status.eq.parsing,lease_until.lt.{now_iso})")
                .order("created_at", desc=False)
                .limit(1)
                .execute()
            )

            if not res.data or len(res.data) == 0:
                return None

            job = res.data[0]
            job_id = job["id"]

            # Attempt atomic lease acquisition
            update_res = (
                self.supabase_client.table("processing_jobs")
                .update({
                    "status": "parsing",
                    "worker_id": WORKER_ID,
                    "lease_until": lease_until_iso,
                    "last_heartbeat_at": now_iso,
                    "current_step": "Claimed by worker...",
                    "progress_percentage": 5
                })
                .eq("id", job_id)
                .execute()
            )

            if update_res.data and len(update_res.data) > 0:
                logger.info(f"[IngestionWorker] Claimed job {job_id} on worker {WORKER_ID}")
                return update_res.data[0]
            return None
        except Exception as e:
            logger.error(f"[IngestionWorker] Error acquiring job: {e}")
            return None

    async def send_heartbeat(self, job_id: str):
        """Update job heartbeat and extend lease timestamp."""
        now_iso = datetime.now(timezone.utc).isoformat()
        lease_until_iso = (datetime.now(timezone.utc) + timedelta(seconds=LEASE_DURATION_SECONDS)).isoformat()
        try:
            self.supabase_client.table("processing_jobs").update({
                "last_heartbeat_at": now_iso,
                "lease_until": lease_until_iso
            }).eq("id", job_id).eq("worker_id", WORKER_ID).execute()
        except Exception as e:
            logger.warning(f"[IngestionWorker] Heartbeat failed for job {job_id}: {e}")

    async def run_worker_loop(self):
        """Main worker loop."""
        self.running = True
        logger.info(f"[IngestionWorker] Starting worker loop {WORKER_ID}")
        while self.running:
            job = await self.acquire_job()
            if job:
                job_id = job["id"]
                try:
                    # Run heartbeat task in background
                    heartbeat_task = asyncio.create_task(self._heartbeat_loop(job_id))
                    
                    # Fetch file from storage or buffer if available
                    # Download file from storage bucket if storage_path exists
                    storage_path = job.get("storage_path") or f"{job['user_id']}/{job_id}/{job['filename']}"
                    file_data = self.supabase_client.storage.from_("financial-pdfs").download(storage_path)
                    
                    import io
                    file_buffer = io.BytesIO(file_data)

                    result = await self.pipeline.run(
                        pdf_file_buffer=file_buffer,
                        user_id=uuid.UUID(job["user_id"]),
                        original_filename=job["filename"],
                        doc_type=job["filename"].split(".")[-1],
                        job_id=uuid.UUID(job_id)
                    )

                    heartbeat_task.cancel()

                    if result.get("success"):
                        self.supabase_client.table("processing_jobs").update({
                            "status": "completed",
                            "current_step": "Complete!",
                            "progress_percentage": 100,
                            "document_id": str(result.get("document_id")),
                            "result_data": result,
                            "completed_at": "now()"
                        }).eq("id", job_id).execute()
                    else:
                        self.supabase_client.table("processing_jobs").update({
                            "status": "failed",
                            "error_message": result.get("message", "Processing failed"),
                            "completed_at": "now()"
                        }).eq("id", job_id).execute()

                except Exception as e:
                    logger.exception(f"[IngestionWorker] Job execution failed for {job_id}")
                    self.supabase_client.table("processing_jobs").update({
                        "status": "failed",
                        "error_message": f"Worker execution error: {str(e)}",
                        "completed_at": "now()"
                    }).eq("id", job_id).execute()
            else:
                await asyncio.sleep(3.0)

    async def _heartbeat_loop(self, job_id: str):
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
            await self.send_heartbeat(job_id)

if __name__ == "__main__":
    worker = IngestionWorker()
    asyncio.run(worker.run_worker_loop())
