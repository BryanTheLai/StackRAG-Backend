import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..dependencies import Session, get_session


class FunctionCall(BaseModel):
    name: str
    args: Dict[str, Any]


class FunctionResponse(BaseModel):
    name: str
    response: Dict[str, Any]


class MessagePart(BaseModel):
    text: str | None = None
    function_call: FunctionCall | None = None
    function_response: FunctionResponse | None = None


class HistoryTurn(BaseModel):
    role: str  # "user", "model", or "function"
    parts: List[MessagePart]


class ChatPayload(BaseModel):
    history: List[HistoryTurn] = Field(
        ..., description="Complete conversation history including the latest user message."
    )


class ChatService:
    async def generate_response_stream(
        self, user_id: str, history: List[HistoryTurn]
    ) -> AsyncGenerator[str, None]:
        """Generate streaming chat response based on conversation history."""
        if not history:
            yield "Error: Conversation history is empty."
            return

        # Get last message for context
        last = history[-1]
        summary = "the last message"
        if last.parts and last.parts[0].text:
            summary = f"user text '{last.parts[0].text[:30]}...'"

        # Simulate streaming response
        await asyncio.sleep(0.1)
        
        response_text = f"Model reply to {summary}: This is a streamed dummy response. "
        for char in response_text:
            yield char
            await asyncio.sleep(0.02)
        
        yield "Stream complete."


router = APIRouter(prefix="/chat", tags=["chat"])
chat_service = ChatService()


@router.post("/stream")
async def stream_chat_response(
    payload: ChatPayload,
    session: Session = Depends(get_session)
):
    """Stream a chat response using server-sent events."""
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for chunk in chat_service.generate_response_stream(
                session.user_id, payload.history
            ):
                data = json.dumps({"text_chunk": chunk})
                yield f"data: {data}\n\n"
            yield "event: stream_end\ndata: {}\n\n"
        except Exception:
            error = json.dumps({"error": "Internal server error."})
            yield f"event: stream_error\ndata: {error}\n\n"
            yield "event: stream_end\ndata: {}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
