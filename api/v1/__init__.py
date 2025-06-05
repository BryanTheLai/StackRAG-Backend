from fastapi import APIRouter

from .endpoints import chat, items

router = APIRouter(prefix="/v1")

router.include_router(items.router)
router.include_router(chat.router)
