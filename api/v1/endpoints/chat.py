from typing import Any, Generator, Dict, List
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from supabase import create_client

from ..dependencies import Session, get_session
from src.llm.workflow.react_rag import run_react_rag
from api.v1.dependencies import SUPABASE_URL, SUPABASE_KEY


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


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/stream")
async def stream_chat_response(
    payload: ChatPayload,
    session: Session = Depends(get_session)
) -> StreamingResponse:
    """Stream a chat response using server-sent events via RAG agent."""
    async def event_generator():
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        try:
            # Extract latest user message text
            user_input = payload.history[-1].parts[0].text

            # Stream responses from RAG agent
            async for message in run_react_rag(session, supabase_client, user_input, payload.history):
                data = json.dumps({"text_chunk": message})
                yield f"data: {data}\n\n"
            yield "event: stream_end\ndata: {}\n\n"
        except Exception as e:
            error = json.dumps({"error": str(e)})
            yield f"event: stream_error\ndata: {error}\n\n"
            yield "event: stream_end\ndata: {}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
