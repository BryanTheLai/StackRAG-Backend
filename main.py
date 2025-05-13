from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, AsyncGenerator, Annotated
import asyncio
import json

# --- Pydantic Models for Chat ---
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
    role: str           # e.g. "user", "model", or "function"
    parts: List[MessagePart]

class ChatPayload(BaseModel):
    history: List[HistoryTurn] = Field(
        ..., description="Complete conversation history including the latest user message."
    )

# --- Authentication Dependency ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user_id_from_token(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> str:
    """
    Verify JWT and return user_id.
    In production, decode and validate signature, claims, etc.
    """
    if token == "valid_jwt_token_for_user_123":
        return "test_user_123"
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

# --- Simulated Chat Service ---
class ChatService:
    async def generate_response_stream(
        self, user_id: str, full_history: List[HistoryTurn]
    ) -> AsyncGenerator[str, None]:
        """
        Yield chunks of a dummy model response based on conversation history.
        """
        if not full_history:
            yield "Error: Conversation history is empty."
            return

        # Summarize the last message for simulation
        last = full_history[-1]
        summary = "the last message"
        if last.parts:
            part = last.parts[0]
            if part.text:
                summary = f"user text '{part.text[:30]}...'"
            elif part.function_call:
                summary = f"function call '{part.function_call.name}'"
            elif part.function_response:
                summary = f"function response '{part.function_response.name}'"

        await asyncio.sleep(0.1)

        header = f"Model reply to {summary}: "
        for ch in header:
            yield ch
            await asyncio.sleep(0.02)

        for word in ["This ", "is ", "a ", "streamed ", "dummy ", "response. "]:
            yield word
            await asyncio.sleep(0.05)

        yield "Stream complete."

# --- FastAPI App Configuration ---
app = FastAPI(
    title="AI CFO Assistant - Chat API",
    version="1.0.0",
    description="Chat endpoint with server-sent events."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "127.0.0.1"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

chat_service_instance = ChatService()
def get_chat_service() -> ChatService:
    return chat_service_instance

# --- Streaming Chat Endpoint ---
@app.post(
    "/v1/chat/stream_response",
    summary="Stream a chat response",
    response_description="SSE stream of text chunks."
)
async def stream_chat_response(
    payload: ChatPayload,
    user_id: Annotated[str, Depends(get_current_user_id_from_token)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)]
):
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for chunk in chat_service.generate_response_stream(user_id, payload.history):
                data = json.dumps({"text_chunk": chunk})
                yield f"data: {data}\n\n"
            yield "event: stream_end\ndata: {}\n\n"
        except HTTPException:
            raise
        except Exception:
            error = json.dumps({"error": "Internal server error."})
            yield f"event: stream_error\ndata: {error}\n\n"
            yield "event: stream_end\ndata: {}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)