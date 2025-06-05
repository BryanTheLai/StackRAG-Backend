import os
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from supabase import create_client  # removed SyncClient import
from api.v1.dependencies import SUPABASE_KEY, SUPABASE_URL, Session
from src.llm.tools.FunctionCaller import RetrievalService
from src.llm.tools.PythonCalculatorTool import PythonCalculationTool
from typing import AsyncGenerator, Any
from src.llm.OpenAIClient import OpenAIClient
from src.storage.SupabaseService import SupabaseService

SYSTEM_PROMPT = """
You are a RAG-enabled AI assistant. You have access to two tools:
 - RetrievalService: retrieve relevant document chunks based on a query.
 - PythonCalculationTool: perform Python calculations.
Use tools as needed and respond with a final answer. Do not invent facts.
"""

async def run_react_rag(
    session: Session,
    supabase_client: Any,
    user_input: str,
    message_history: list = None
) -> AsyncGenerator[str, None]:
    print(f"[DEBUG] run_react_rag called with session.user_id={session.user_id}, user_input={user_input}, history_len={(len(message_history) if message_history else 0)}")
    # authenticate on each call
    supabase_client.options.headers["Authorization"] = f"Bearer {session.token}"
    user_id = session.user_id

    # initialize tools
    retrieval = RetrievalService(
        openai_client=OpenAIClient(),
        supabase_service = SupabaseService(supabase_client=supabase_client),
        user_id=user_id
    )
    calculator = PythonCalculationTool()
    
    provider = GoogleProvider(api_key=os.environ.get("GEMINI_API_KEY"))
    model = GoogleModel('gemini-2.5-flash-preview-05-20', provider=provider)

    agent = Agent(
        model,
        tools=[
            retrieval.retrieve_chunks,
            calculator.execute_python_calculations
        ],
        system_prompt=SYSTEM_PROMPT,
        streaming=True,
    )

    # stream and yield results incrementally with debug
    try:
        async with agent.run_stream(user_input) as result:  
            async for message in result.stream_text(delta=True):                  
                print(f"[DEBUG] message received: {message}")
                yield message
    except Exception as e:
        print(f"[ERROR] run_react_rag exception: {e}", flush=True)
        yield f"(Error in run_react_rag: {e})"
        return
    print("[DEBUG] run_react_rag completed streaming", flush=True)

if __name__ == '__main__':
    import sys
    import os
    project_root = os.path.abspath(os.path.join(os.getcwd(), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    import asyncio
    # Test run_react_rag function
    session = Session(user_id='test_user', token=SUPABASE_KEY)
    test_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    async def main_test():
        print('[TEST] Starting run_react_rag test')
        async for chunk in run_react_rag(session, test_client, 'Hello RAG test', []):
            print(f'[TEST] Received chunk: {chunk}')
        print('[TEST] run_react_rag test completed')
    asyncio.run(main_test())