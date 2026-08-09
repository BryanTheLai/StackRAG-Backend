from fastapi import APIRouter
from .endpoints import chat, document_process, health

router = APIRouter(prefix="/v1")


router.include_router(chat.router)
router.include_router(document_process.router)
router.include_router(health.router)


