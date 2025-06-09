import os
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_core import to_jsonable_python
from pydantic_ai.messages import ModelMessagesTypeAdapter  
from supabase import create_client  # removed SyncClient import
from api.v1.dependencies import SUPABASE_KEY, SUPABASE_URL, Session
from src.llm.tools.FunctionCaller import RetrievalService
from src.llm.tools.PythonCalculatorTool import PythonCalculationTool
from typing import AsyncGenerator, Any
from src.llm.OpenAIClient import OpenAIClient
from src.storage.SupabaseService import SupabaseService

SYSTEM_PROMPT = """
You are a financial document analysis AI assistant with access to the user's uploaded financial documents.
Your primary goal is to help users understand and analyze financial information from their documents.

REMEMBERING USER DETAILS:
- CRITICAL INSTRUCTION: If the user tells you their name, you MUST remember it for the duration of this session.
- When appropriate, use the user's name to personalize the conversation. For example, if the user says 'My name is Alze', and later asks 'What is my name?', you MUST reply 'Your name is Alze.' If they ask a general question, you might start your response with 'Certainly, Alze, ...'.

IMPORTANT INSTRUCTIONS (Financial Analysis):
1. ALWAYS use the retrieve_financial_chunks tool to search for information before answering questions about financial data.
2. Be specific and accurate - only provide information that you can find in the retrieved documents.
3. If you cannot find relevant information in the documents, clearly state this.
4. Use the Python calculator tool for any mathematical calculations or financial metric computations.
5. Provide clear, well-structured responses with specific references to the documents when possible.

When users ask about:
- Financial metrics, ratios, or performance indicators
- Company financial data or trends
- Specific information from financial statements
- Comparisons between time periods or companies
- Any other financial document content

You should FIRST search for relevant information using the retrieve_financial_chunks tool,
then provide a comprehensive answer based on the retrieved content.
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

    # ensure message_history is JSON serializable
    history_for_model = to_jsonable_python(message_history) if message_history else []
    same_history_as_step_1 = ModelMessagesTypeAdapter.validate_python(history_for_model)
    print(same_history_as_step_1)

    # Instantiate agent including prior chat context
    agent = Agent(
        model,
        tools=[retrieval.retrieve_chunks, calculator.execute_python_calculations],
        system_prompt=SYSTEM_PROMPT,
        streaming=True,
        message_history=same_history_as_step_1
    )

    # stream and yield results incrementally with debug
    try:
        async with agent.run_stream(user_input, message_history=same_history_as_step_1) as result:  
            async for message in result.stream_text(delta=True):                  
                print(f"[DEBUG] message received: {message}")
                yield message
    except Exception as e:
        import traceback
        # Print full stack trace for debugging
        traceback.print_exc()
        print(f"[ERROR] run_react_rag exception: {repr(e)}", flush=True)
        yield f"(Error in run_react_rag: {repr(e)})"
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