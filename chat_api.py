from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, AsyncGenerator, Annotated
import asyncio
import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL") or exit("Error: SUPABASE_URL must be set")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or exit("Error: SUPABASE_ANON_KEY must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

class Session(BaseModel):
    user_id: str
    token: str
# --- Authentication Dependency ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_session(token: str = Depends(oauth2_scheme)) -> Session:
    if not token:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        res = supabase.auth.get_user(jwt=token)
        user = res.user
        if not user or not user.id:
            raise ValueError("Invalid user")
        print(f"Backend: Token validated for user {user.id}")
        return Session(user_id=user.id, token=token)
    except Exception as e:
        print(f"Backend: Error validating token: {e}")
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
async def get_current_user_id_from_token(
    session: Annotated[Session, Depends(get_session)]
) -> str:
    """
    Extract and return user_id from a validated Session.
    """
    return session.user_id

# --- Simulated Chat Service ---
class ChatService:
    async def generate_response_stream(
        self, user_id: str, full_history: List[HistoryTurn]
    ) -> AsyncGenerator[str, None]:
        """
        Yield chunks of a dummy model response based on conversation history.
        """
        print(f"User ID: {user_id}")
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