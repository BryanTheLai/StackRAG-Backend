from typing import Any, Generator, Dict, List
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from supabase import create_client
# Add pydantic-ai message imports
from pydantic_ai.messages import UserPromptPart, SystemPromptPart, TextPart, ToolCallPart, ToolReturnPart, ModelRequest, ModelResponse

from ..dependencies import Session, get_session
from src.llm.workflow.react_rag import run_react_rag
from api.v1.dependencies import SUPABASE_URL, SUPABASE_KEY


class MessagePart(BaseModel):
    content: str
    timestamp: str | None = None
    dynamic_ref: Any | None = None
    part_kind: str  # "system-prompt", "user-prompt", "text"


class HistoryTurn(BaseModel):
    parts: List[MessagePart]
    instructions: Any | None = None
    kind: str  # "request" or "response"
    usage: Dict[str, Any] | None = None
    model_name: str | None = None
    timestamp: str | None = None
    vendor_details: Any | None = None
    vendor_id: str | None = None


class ChatPayload(BaseModel):
    history: List[HistoryTurn] = Field(
        ..., description="Complete conversation history including the latest user message."
    )

# Helper function to convert frontend history to pydantic-ai format
def convert_history_to_pydantic_ai_format(history: List[HistoryTurn]) -> list:
    pydantic_ai_history = []
    for turn in history:
        parts = []
        for part_data in turn.parts:
            if part_data.part_kind == "system-prompt" and part_data.content:
                parts.append(SystemPromptPart(content=part_data.content))
            elif part_data.part_kind == "user-prompt" and part_data.content:
                parts.append(UserPromptPart(content=part_data.content))
            elif part_data.part_kind == "text" and part_data.content: # Model text response
                parts.append(TextPart(content=part_data.content))

        if not parts: # Skip if no valid parts were created for this turn
            continue

        if turn.kind == "request": # Corresponds to ModelRequest
            # A ModelRequest can have system and user prompts together
            pydantic_ai_history.append(ModelRequest(parts=parts))
        elif turn.kind == "response": # Corresponds to ModelResponse
            # A ModelResponse typically has one main part (TextPart, ToolCallPart)
            # For simplicity, assuming the first valid part is the primary one for ModelResponse
            pydantic_ai_history.append(ModelResponse(parts=parts))
    return pydantic_ai_history


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
            # Assuming the last message in history is the current user input
            # And it's the first part of that message
            user_input = ""
            if payload.history and payload.history[-1].parts:
                 # Find the user-prompt part in the last history turn
                for part in payload.history[-1].parts:
                    if part.part_kind == "user-prompt" and part.content:
                        user_input = part.content
                        break
            
            if not user_input: # Fallback or error if no user input found
                user_input = "Hello" # Or raise an error

            # Convert history to pydantic-ai format
            # We pass all history *except* the last user message, as that's the new input
            formatted_history = convert_history_to_pydantic_ai_format(payload.history[:-1])

            # Stream responses from RAG agent
            async for message in run_react_rag(session, supabase_client, user_input, formatted_history):
                data = json.dumps({"text_chunk": message})
                yield f"data: {data}\n\n"
            yield "event: stream_end\ndata: {}\n\n"
        except Exception as e:
            error = json.dumps({"error": str(e)})
            yield f"event: stream_error\ndata: {error}\n\n"
            yield "event: stream_end\ndata: {}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
