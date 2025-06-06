from fastapi import APIRouter

from .endpoints import chat, items, document_process

router = APIRouter(prefix="/v1")

router.include_router(items.router)
router.include_router(chat.router)
router.include_router(document_process.router)
