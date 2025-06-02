from typing import Any, Generator, Dict, List
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..dependencies import Session, get_session
from src.llm.GeminiClient import GeminiClient
from src.config.gemini_config import DEFAULT_CHAT_MODEL


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
    def generate_response_stream(
        self, user_id: str, history: List[HistoryTurn]
    ) -> Generator[str, None, None]:
        """Generate streaming chat response based on conversation history using Gemini."""
        if not history:
            yield "Error: Conversation history is empty."
            return

        # Ensure the last message is from the user and has text content.
        last_turn = history[-1]
        if last_turn.role != "user" or not last_turn.parts or not last_turn.parts[0].text:
            yield "Error: Conversation history must end with a user message with text content."
            return

        try:
            from src.helper.llm_helper_chat import serialize_conversation_history

            gemini_client = GeminiClient()
            history_payload = serialize_conversation_history(history)
            message = json.dumps(history_payload)
            # Stream content generation directly
            for chunk in gemini_client.generate_content_stream(DEFAULT_CHAT_MODEL, [message]):
                # Extract text from stream chunk
                text = getattr(chunk, 'text', None)
                if not text and hasattr(chunk, 'candidates'):
                    first_cand = chunk.candidates[0]
                    text = getattr(first_cand, 'text', getattr(first_cand, 'content', None))
                if text:
                    yield text
        except ValueError as ve:
            yield f"Error: Configuration error - {str(ve)}"
        except Exception:
            raise


router = APIRouter(prefix="/chat", tags=["chat"])
chat_service = ChatService()


@router.post("/stream")
def stream_chat_response(
    payload: ChatPayload,
    session: Session = Depends(get_session)
):
    """Stream a chat response using server-sent events."""
    def event_generator() -> Generator[str, None, None]:
        try:
            for chunk in chat_service.generate_response_stream(
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
