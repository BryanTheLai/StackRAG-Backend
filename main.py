from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, AsyncGenerator, Annotated
import asyncio
import json

# --- Pydantic Models for input validation ---
class MessagePart(BaseModel):
    text: str | None = None
    function_call: Dict[str, Any] | None = None
    function_response: Dict[str, Any] | None = None

class HistoryTurn(BaseModel):
    role: str
    parts: List[MessagePart]

class ChatContextPayload(BaseModel): # Renamed for clarity
    conversation_context: List[HistoryTurn] = Field(
        ...,
        description="The complete conversation history including the latest user message."
    )

# --- Dummy User Auth ---
async def get_current_user_id() -> str:
    print("Backend: get_current_user_id called")
    return "test_user_123"

# --- FastAPI App Setup ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dummy LLM Interaction (Simulated) ---
async def dummy_llm_streamer(
    user_id: str,
    full_conversation_context: List[HistoryTurn] # Now takes the full context
) -> AsyncGenerator[str, None]:
    print(f"\nBackend: Received full context for user '{user_id}':")
    # For debugging, print the full context received
    # print(f"Backend: Full Context JSON: {json.dumps([turn.model_dump() for turn in full_conversation_context], indent=2)}")


    if not full_conversation_context or full_conversation_context[-1].role != "user":
        yield "Error: Last message in context is not from user or context is empty."
        print("Backend Error: Last message not from user or context empty.")
        return

    current_user_message_turn = full_conversation_context[-1]
    current_user_message_text = ""
    if current_user_message_turn.parts and current_user_message_turn.parts[0].text:
        current_user_message_text = current_user_message_turn.parts[0].text
    
    print(f"Backend: Simulating response to user's last message: '{current_user_message_text}'")
    print(f"Backend: Full history for LLM has {len(full_conversation_context)} turns.")


    await asyncio.sleep(0.2) # Simulate processing time

    # This part simulates the LLM generating ONLY the new response text
    simulated_response_prefix = f"Model's new reply to '{current_user_message_text[:20]}...': "
    for char_chunk in simulated_response_prefix:
        yield char_chunk
        await asyncio.sleep(0.03) # Slower for prefix

    words = ["This ", "is ", "the ", "streamed ", "model ", "output ", "only. "]
    for word in words:
        yield word
        await asyncio.sleep(0.08) # Slower for words
    yield "Done streaming new reply!"


# --- API Endpoint ---
@app.post("/simple_chat_context_test") # Renamed endpoint for clarity
async def handle_simple_chat_context_test(
    payload: ChatContextPayload, # Use the new Pydantic model
    user_id: Annotated[str, Depends(get_current_user_id)]
):
    print(f"Payload: \n{payload.model_dump_json(indent=2)}\n")
    print(f"Backend: Received payload for user '{user_id}':")
    # print(payload.model_dump_json(indent=2)) # For debugging the received payload

    async def sse_event_stream() -> AsyncGenerator[str, None]:
        async for token_text_chunk in dummy_llm_streamer(
            user_id=user_id,
            full_conversation_context=payload.conversation_context # Pass the whole context
        ):
            sse_formatted_data = f"data: {json.dumps({'text_chunk': token_text_chunk})}\n\n"
            yield sse_formatted_data
            # print(f"Backend: Sent chunk: {token_text_chunk}") # Can be noisy

        yield "event: end_stream\ndata: {}\n\n"
        print("Backend: Sent end_stream event")

    return StreamingResponse(sse_event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)