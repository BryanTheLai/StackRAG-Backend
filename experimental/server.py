from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio

app = FastAPI()

async def simulate_rag_stream():
    print("Server: Starting stream simulation...")

    yield "event: status\ndata: Query received. Checking for tools...\n\n"
    await asyncio.sleep(0.5)

    yield "event: status\ndata: Retrieving relevant documents...\n\n"
    await asyncio.sleep(1.5)
    yield "event: retrieved_sources\ndata: [{\"title\": \"Annual Report 2023\", \"page\": 5}]\n\n"

    yield "event: status\ndata: Ranking search results...\n\n"
    await asyncio.sleep(0.8)

    yield "event: status\ndata: Generating answer...\n\n"
    await asyncio.sleep(0.5)

    yield "event: status\ndata: Generating Sources...\n\n"
    await asyncio.sleep(0.5)

    dummy_answer_tokens = [
        "Based", " on", " the", " documents", ",", " the", " total", " revenue", " in", " 2023", " was", " $", "10", ",", "000", ",", "000", "."
    ]

    for token in dummy_answer_tokens:
        yield f"event: token\ndata: {token}\n\n"
        await asyncio.sleep(0.2)

    yield "event: citation\ndata: [Source: Annual Report 2023, p. 10]\n\n"
    yield "event: end\ndata: Simulation complete.\n\n"
    print("Server: Stream simulation finished.")

@app.get("/stream")
async def stream_endpoint():
    return StreamingResponse(
        simulate_rag_stream(),
        media_type="text/event-stream"
    )