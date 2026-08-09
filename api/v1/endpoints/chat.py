from typing import Any, AsyncGenerator, Dict, List, Optional
import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from supabase import create_client

from ..dependencies import Session, get_session, SUPABASE_URL, SUPABASE_KEY
from src.llm.workflow.react_rag import run_react_rag


logger = logging.getLogger("uvicorn.error")


class ChatStreamPayload(BaseModel):
    session_id: Optional[str] = Field(
        None, description="Optional chat session ID. If omitted, a new session will be created."
    )
    message: str = Field(..., min_length=1, description="The user message to send.")


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/stream")
async def stream_chat_response(
    payload: ChatStreamPayload,
    session: Session = Depends(get_session)
) -> StreamingResponse:
    """Stream a chat response using server-sent events with server-owned session memory."""
    user_id = session.user_id
    token = session.token
    message_text = payload.message.strip()

    if not message_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message text cannot be empty."
        )

    request_id = str(uuid.uuid4())

    async def event_generator() -> AsyncGenerator[str, None]:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        supabase_client.options.headers["Authorization"] = f"Bearer {token}"

        session_id = payload.session_id
        history: List[Dict[str, Any]] = []

        try:
            if session_id:
                # Load server-owned session history from database enforcing RLS user ownership
                res = (
                    supabase_client.table("chat_sessions")
                    .select("*")
                    .eq("id", session_id)
                    .eq("user_id", user_id)
                    .execute()
                )
                if res.data and len(res.data) > 0:
                    history = res.data[0].get("history") or []
                else:
                    error_json = json.dumps({
                        "error_code": "SESSION_NOT_FOUND",
                        "message": "Chat session not found or access denied",
                        "request_id": request_id
                    })
                    yield f"event: message.failed\ndata: {error_json}\n\n"
                    return
            else:
                # Create new session record
                new_session_id = str(uuid.uuid4())
                title = message_text[:40] + ("..." if len(message_text) > 40 else "")
                supabase_client.table("chat_sessions").insert({
                    "id": new_session_id,
                    "user_id": user_id,
                    "title": title,
                    "history": []
                }).execute()
                session_id = new_session_id

            # Emit initial event
            yield f"event: message.started\ndata: {json.dumps({'request_id': request_id, 'session_id': session_id})}\n\n"

            acc_response = ""
            citations: List[Dict[str, Any]] = []

            # Stream model & tool events
            async for event_type, data in run_react_rag(
                session=session,
                supabase_client=supabase_client,
                user_input=message_text,
                history_turns=history
            ):
                if event_type == "delta":
                    acc_response += data.get("text", "")
                    yield f"event: message.delta\ndata: {json.dumps({'delta': data.get('text', '')})}\n\n"
                elif event_type == "tool.started":
                    yield f"event: tool.started\ndata: {json.dumps(data)}\n\n"
                elif event_type == "tool.completed":
                    yield f"event: tool.completed\ndata: {json.dumps(data)}\n\n"
                elif event_type == "citation.added":
                    citations.append(data)
                    yield f"event: citation.added\ndata: {json.dumps(data)}\n\n"
                elif event_type == "ping":
                    yield ": ping\n\n"

            # Save updated conversation turns server-side
            now_iso = datetime.now(timezone.utc).isoformat()
            user_turn = {
                "kind": "request",
                "parts": [{"part_kind": "user-prompt", "content": message_text}],
                "timestamp": now_iso
            }
            assistant_turn = {
                "kind": "response",
                "parts": [{"part_kind": "text", "content": acc_response}],
                "citations": citations,
                "timestamp": now_iso
            }

            updated_history = history + [user_turn, assistant_turn]

            supabase_client.table("chat_sessions").update({
                "history": updated_history,
                "updated_at": "now()"
            }).eq("id", session_id).eq("user_id", user_id).execute()

            # Emit message.completed event
            yield f"event: message.completed\ndata: {json.dumps({'request_id': request_id, 'session_id': session_id, 'citation_count': len(citations)})}\n\n"

        except Exception as e:
            logger.exception("chat_stream_exception request_id=%s session_id=%s", request_id, session_id)
            error_payload = {
                "error_code": "CHAT_STREAM_ERROR",
                "message": "An error occurred while generating the chat response. Please try again.",
                "request_id": request_id
            }
            yield f"event: message.failed\ndata: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

