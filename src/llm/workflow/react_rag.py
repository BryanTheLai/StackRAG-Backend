import os
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_core import to_jsonable_python
from pydantic_ai.messages import ModelMessagesTypeAdapter  
from supabase import create_client
from api.v1.dependencies import SUPABASE_KEY, SUPABASE_URL, Session
from src.llm.tools.FunctionCaller import RetrievalService
from src.llm.tools.PythonCalculatorTool import PythonCalculationTool
from typing import AsyncGenerator, Any
from src.llm.OpenAIClient import OpenAIClient
from src.storage.SupabaseService import SupabaseService
from src.prompts.prompt_manager import PromptManager
from src.config.gemini_config import DEFAULT_CHAT_MODEL
from datetime import datetime, timezone

def create_system_prompt(**user_details):
    return PromptManager.get_prompt(
        "chat_system_prompt",
        APP_DOMAIN=user_details.get("APP_DOMAIN", "https://stackifier.com"),
        FULL_NAME=user_details.get("FULL_NAME", ""),
        COMPANY_NAME=user_details.get("COMPANY_NAME", ""),
        ROLE_IN_COMPANY=user_details.get("ROLE_IN_COMPANY", ""),
        CURRENT_DATE=user_details.get("CURRENT_DATE", "")
    )

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
    # get current date for system prompt (timezone-aware UTC)
    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # fetch user profile for system prompt
    try:
        profile_resp = supabase_client.table('profiles')\
            .select('full_name, company_name, role_in_company')\
            .eq('id', user_id)\
            .single()\
            .execute()
        profile_data = profile_resp.data or {}
    except Exception:
        profile_data = {}
    # debug profile_data
    print(f"[DEBUG] profile_data: {profile_data}")
    # generate dynamic system prompt with current date
    system_prompt = create_system_prompt(
        APP_DOMAIN="https://stackifier.com",
        FULL_NAME=profile_data.get("full_name", ""),
        COMPANY_NAME=profile_data.get("company_name", ""),
        ROLE_IN_COMPANY=profile_data.get("role_in_company", ""),
        CURRENT_DATE=current_date
    )
    print(f"[DEBUG] system_prompt: {system_prompt}")
    # initialize tools
    retrieval = RetrievalService(
        openai_client=OpenAIClient(),
        supabase_service=SupabaseService(supabase_client=supabase_client),
        user_id=user_id
    )
    calculator = PythonCalculationTool()
    # Ensure GEMINI_API_KEY is set and retrieve directly for str type
    if "GEMINI_API_KEY" not in os.environ:
        raise EnvironmentError("GEMINI_API_KEY must be set as an environment variable")
    gemini_key = os.environ["GEMINI_API_KEY"]
    provider = GoogleProvider(api_key=gemini_key)
    model = GoogleModel(DEFAULT_CHAT_MODEL, provider=provider)

    # ensure message_history is JSON serializable
    history_for_model = to_jsonable_python(message_history) if message_history else []  # use only user and assistant messages
    same_history_as_step_1 = ModelMessagesTypeAdapter.validate_python(history_for_model)

    # Instantiate agent with keyword args to satisfy signature
    agent = Agent(
        model=model,
        tools=[retrieval.retrieve_chunks, calculator.execute_python_calculations],
        instructions=system_prompt,
        streaming=True,
        message_history=same_history_as_step_1
    )

    # stream and yield results incrementally with debug
    try:
        async with agent.run_stream(user_input, message_history=same_history_as_step_1) as result:  
            async for message in result.stream_text(delta=True):                  
                print(f"{message}")
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
    # Ensure Supabase credentials and cast to str to satisfy type
    assert SUPABASE_URL and SUPABASE_KEY, "SUPABASE_URL and SUPABASE_KEY must be set"
    session = Session(user_id='test_user', token=str(SUPABASE_KEY))
    test_client = create_client(str(SUPABASE_URL), str(SUPABASE_KEY))
    async def main_test():
        print('[TEST] Starting run_react_rag test')
        async for chunk in run_react_rag(session, test_client, 'Hello RAG test', []):
            print(f'[TEST] Received chunk: {chunk}')
        print('[TEST] run_react_rag test completed')
    asyncio.run(main_test())