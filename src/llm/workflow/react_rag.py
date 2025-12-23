"""RAG Agent Workflow with configurable chat providers.

Chat provider selection is controlled by environment variables:
- CHAT_PROVIDER: "gemini" (default) or "openai"
- GEMINI_CHAT_MODEL: overrides the default Gemini model
- OPENAI_CHAT_MODEL: overrides the default OpenAI chat model

Note: document retrieval currently uses OpenAI embeddings via OpenAIClient.
"""

import os
import sys
import asyncio
import traceback
import json
from typing import TYPE_CHECKING
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_core import to_jsonable_python
from pydantic_ai.messages import ModelMessagesTypeAdapter  
from supabase import create_client
from src.llm.tools.FunctionCaller import RetrievalService
from src.llm.tools.PythonCalculatorTool import PythonCalculationTool
from typing import AsyncGenerator, Any
from src.llm.OpenAIClient import OpenAIClient
from src.storage.SupabaseService import SupabaseService
from src.prompts.prompt_manager import PromptManager
from src.config.gemini_config import DEFAULT_CHAT_MODEL
#from src.config.openai_config import DEFAULT_CHAT_MODEL
from datetime import datetime, timezone
from src.config.site import APP_DOMAIN

# Configuration for provider selection - Change this to switch providers
CHAT_PROVIDER = os.environ.get("CHAT_PROVIDER", "gemini").strip().lower()
OPENAI_MODEL_NAME = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4.1-mini-2025-04-14")
GEMINI_MODEL_NAME = os.environ.get("GEMINI_CHAT_MODEL", DEFAULT_CHAT_MODEL)

print(
    "[DEBUG] LLM config: "
    f"CHAT_PROVIDER={CHAT_PROVIDER} "
    f"GEMINI_CHAT_MODEL={GEMINI_MODEL_NAME} "
    f"OPENAI_CHAT_MODEL={OPENAI_MODEL_NAME} "
    f"GEMINI_API_KEY={'set' if 'GEMINI_API_KEY' in os.environ else 'missing'} "
    f"OPENAI_API_KEY={'set' if 'OPENAI_API_KEY' in os.environ else 'missing'}"
    ,
    flush=True,
)

CHART_OPEN_TAG = "<ChartData>"
CHART_CLOSE_TAG = "</ChartData>"
PDFNAV_OPEN_TAG = "<PDFNav>"
PDFNAV_CLOSE_TAG = "</PDFNav>"

_VIZ_KEYWORDS = (
    "plot",
    "chart",
    "graph",
    "visualize",
    "visualise",
    "trend",
)


if TYPE_CHECKING:
    from api.v1.dependencies import Session


def _has_block(text: str, open_tag: str, close_tag: str) -> bool:
    if not text:
        return False
    start = text.find(open_tag)
    if start == -1:
        return False
    end = text.find(close_tag, start + len(open_tag))
    return end != -1


def _should_require_visual_chart(user_input: str) -> bool:
    s = (user_input or "").lower()
    return any(k in s for k in _VIZ_KEYWORDS)


def _chunk_text_for_sse(text: str, chunk_size: int = 80):
    if not text:
        return
    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]


def _placeholder_chart(title: str = "Chart") -> str:
    payload = {
        "type": "line",
        "title": title,
        "data": [{"name": "(no data)", "value": 0}],
        "metadata": {"note": "placeholder"},
    }
    return f"\n{CHART_OPEN_TAG}\n{json.dumps(payload)}\n{CHART_CLOSE_TAG}\n"


def _placeholder_pdfnav(context: str = "No document available for citation.") -> str:
    payload = {
        "documentId": "",
        "filename": "",
        "page": 1,
        "context": context,
    }
    return f"\n{PDFNAV_OPEN_TAG}\n{json.dumps(payload)}\n{PDFNAV_CLOSE_TAG}\n"


def _best_effort_pdfnav_from_retrieval_json(retrieval_json: str) -> dict | None:
    """Extract a reasonable PDFNav payload from retrieved chunks JSON."""
    if not retrieval_json:
        return None
    try:
        data = json.loads(retrieval_json)
    except Exception:
        return None

    if not isinstance(data, list) or not data:
        return None

    for item in data:
        if not isinstance(item, dict):
            continue
        document_id = item.get("document_id") or item.get("documentId")
        filename = item.get("document_filename") or item.get("filename") or item.get("document_name")
        page = (
            item.get("page")
            or item.get("page_number")
            or item.get("page_start")
            or item.get("pageIndex")
        )
        if isinstance(page, str) and page.isdigit():
            page = int(page)
        if not isinstance(page, int):
            page = 1

        context = (
            item.get("chunk_text")
            or item.get("content")
            or item.get("text")
            or item.get("markdown")
            or ""
        )
        context = (context or "").strip()
        if len(context) > 600:
            context = context[:600] + "…"

        if document_id:
            return {
                "documentId": str(document_id),
                "filename": str(filename or ""),
                "page": page,
                "context": context or "Relevant excerpt from retrieved documents.",
            }
    return None


def _retrieval_context_for_prompt(retrieval_json: str, max_chunks: int = 10, max_chars: int = 9000) -> str:
    """Build a compact, model-friendly context block from retrieved chunks JSON."""
    if not retrieval_json:
        return ""
    try:
        data = json.loads(retrieval_json)
    except Exception:
        # If it's not JSON, include as-is but cap length
        return retrieval_json[:max_chars]

    if not isinstance(data, list) or not data:
        return ""

    compact: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        text = (
            item.get("chunk_text")
            or item.get("content")
            or item.get("text")
            or item.get("markdown")
            or ""
        )
        text = (text or "").strip()
        if len(text) > 800:
            text = text[:800] + "…"
        compact.append(
            {
                "document_id": item.get("document_id") or item.get("documentId"),
                "document_filename": item.get("document_filename") or item.get("filename") or item.get("document_name"),
                "page": item.get("page") or item.get("page_number") or item.get("page_start") or 1,
                "text": text,
            }
        )
        if len(compact) >= max_chunks:
            break

    block = json.dumps(compact, ensure_ascii=False, default=str)
    if len(block) > max_chars:
        block = block[:max_chars] + "…"
    return block


def _strip_obvious_plotting_code(text: str) -> str:
    if not text:
        return text
    if "matplotlib" not in text and "plt." not in text:
        return text
    lines = text.splitlines()
    cleaned: list[str] = []
    in_fence = False
    fence_lang = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if not in_fence:
                in_fence = True
                fence_lang = stripped[3:].strip().lower()
                if fence_lang in ("python", "py", ""):
                    continue
            else:
                in_fence = False
                fence_lang = ""
                continue
        if in_fence and fence_lang in ("python", "py", ""):
            continue
        if "matplotlib" in stripped or stripped.startswith("plt."):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()

def create_system_prompt(**user_details):
    return PromptManager.get_prompt(
        "chat_system_prompt",
        APP_DOMAIN=user_details.get("APP_DOMAIN"),
        FULL_NAME=user_details.get("FULL_NAME", ""),
        COMPANY_NAME=user_details.get("COMPANY_NAME", ""),
        ROLE_IN_COMPANY=user_details.get("ROLE_IN_COMPANY", ""),
        CURRENT_DATE=user_details.get("CURRENT_DATE", "")
    )

async def run_react_rag(
    session: Any,
    supabase_client: Any,
    user_input: str,
    message_history: list = None
) -> AsyncGenerator[str, None]:
    print(f"[DEBUG] run_react_rag called (user_id={session.user_id}, history_len={(len(message_history) if message_history else 0)})")
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
    # generate dynamic system prompt with current date and configured domain
    system_prompt = create_system_prompt(
        APP_DOMAIN=APP_DOMAIN,
        FULL_NAME=profile_data.get("full_name", ""),
        COMPANY_NAME=profile_data.get("company_name", ""),
        ROLE_IN_COMPANY=profile_data.get("role_in_company", ""),
        CURRENT_DATE=current_date
    )
    # initialize tools
    retrieval = RetrievalService(
        openai_client=OpenAIClient(),
        supabase_service=SupabaseService(supabase_client=supabase_client),
        user_id=user_id
    )
    #calculator = PythonCalculationTool()
    # Chat model provider configuration (default: Gemini)
    if CHAT_PROVIDER == "openai":
        if "OPENAI_API_KEY" not in os.environ:
            raise EnvironmentError("OPENAI_API_KEY must be set as an environment variable")
        openai_key = os.environ["OPENAI_API_KEY"]
        provider = OpenAIProvider(api_key=openai_key)
        model = OpenAIModel(OPENAI_MODEL_NAME, provider=provider)
        print(f"[DEBUG] Chat provider=openai model={OPENAI_MODEL_NAME}")
    else:
        if "GEMINI_API_KEY" not in os.environ:
            raise EnvironmentError("GEMINI_API_KEY must be set as an environment variable")
        gemini_key = os.environ["GEMINI_API_KEY"]
        provider = GoogleProvider(api_key=gemini_key)
        model = GoogleModel(GEMINI_MODEL_NAME, provider=provider)
        print(f"[DEBUG] Chat provider=gemini model={GEMINI_MODEL_NAME}")

    # ensure message_history is JSON serializable
    history_for_model = to_jsonable_python(message_history) if message_history else []  # use only user and assistant messages
    same_history_as_step_1 = ModelMessagesTypeAdapter.validate_python(history_for_model)

    # IMPORTANT: Gemini tool-calling currently fails with google-genai 400 INVALID_ARGUMENT
    # complaining about missing thought_signature on functionCall parts.
    # Workaround: run retrieval server-side and feed retrieved context to Gemini (no tools).
    retrieval_json: str | None = None
    preferred_pdfnav_payload: dict | None = None
    if CHAT_PROVIDER != "openai":
        try:
            retrieval_json = retrieval.retrieve_chunks(query_text=user_input, match_count=50)
            preferred_pdfnav_payload = _best_effort_pdfnav_from_retrieval_json(retrieval_json)
        except Exception:
            traceback.print_exc()
            retrieval_json = None
            preferred_pdfnav_payload = None

    try:
        augmented_system_prompt = system_prompt
        tools_for_agent = [retrieval.retrieve_chunks] if CHAT_PROVIDER == "openai" else []

        if CHAT_PROVIDER != "openai" and retrieval_json:
            retrieval_block = _retrieval_context_for_prompt(retrieval_json)
            if retrieval_block:
                augmented_system_prompt = (
                    system_prompt
                    + "\n\nYou are provided retrieved document chunks below as JSON. "
                    + "Use them to answer and to produce <PDFNav> with a real documentId/page when possible.\n"
                    + "<RetrievedChunks>\n"
                    + retrieval_block
                    + "\n</RetrievedChunks>\n"
                )

        agent = Agent(
            model=model,
            system_prompt=augmented_system_prompt,
            tools=tools_for_agent,
            output_type=str,
        )

        require_meaningful_chart = _should_require_visual_chart(user_input)

        async def run_once(prompt: str) -> str:
            result = await agent.run(prompt, message_history=same_history_as_step_1)
            return (result.data or "").strip()

        # Attempt 1: normal
        answer = await run_once(user_input)

        # Attempt 2: repair
        if not (_has_block(answer, CHART_OPEN_TAG, CHART_CLOSE_TAG) and _has_block(answer, PDFNAV_OPEN_TAG, PDFNAV_CLOSE_TAG)):
            repair = (
                "\n\nCRITICAL OUTPUT RULE: include BOTH <ChartData>...</ChartData> and <PDFNav>...</PDFNav> in this SAME message. "
                "Do NOT output Python/matplotlib/seaborn code. Use <ChartData> only (no markdown fences)."
            )
            answer = await run_once(user_input + repair)

        # Attempt 3: strict format
        if not (_has_block(answer, CHART_OPEN_TAG, CHART_CLOSE_TAG) and _has_block(answer, PDFNAV_OPEN_TAG, PDFNAV_CLOSE_TAG)):
            strict = (
                "\n\nOUTPUT FORMAT (follow exactly):\n"
                "1) <ChartData>{...}</ChartData>\n"
                "2) <PDFNav>{...}</PDFNav>\n"
                "No Python code. No code fences."
            )
            answer = await run_once(user_input + strict)

        # Last resort cleanup + placeholders
        answer = _strip_obvious_plotting_code(answer)
        if not _has_block(answer, CHART_OPEN_TAG, CHART_CLOSE_TAG):
            title = "Requested Chart" if require_meaningful_chart else "Chart"
            answer += _placeholder_chart(title=title)
        if not _has_block(answer, PDFNAV_OPEN_TAG, PDFNAV_CLOSE_TAG):
            if preferred_pdfnav_payload:
                answer += f"\n{PDFNAV_OPEN_TAG}\n{json.dumps(preferred_pdfnav_payload)}\n{PDFNAV_CLOSE_TAG}\n"
            else:
                answer += _placeholder_pdfnav(
                    context="No valid document citation was produced. Upload documents or refine the query so retrieval can cite sources."
                )

        # Debug: print the full final answer (truncate very large outputs)
        print("\n==================== FINAL MODEL OUTPUT (validated) ====================")
        max_chars = 20000
        if len(answer) > max_chars:
            print(answer[:max_chars])
            print(f"\n... (truncated, total_chars={len(answer)})")
        else:
            print(answer)
        print("=======================================================================\n")

        for chunk in _chunk_text_for_sse(answer, chunk_size=80):
            yield chunk

    except Exception:
        # Keep errors user-friendly; stack trace is still printed server-side.
        traceback.print_exc()
        yield "I encountered an error while generating a response. Please try again."

if __name__ == '__main__':
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_key:
        raise EnvironmentError("Set SUPABASE_URL and SUPABASE_ANON_KEY to run this file directly")

    class _Session:
        def __init__(self, user_id: str, token: str):
            self.user_id = user_id
            self.token = token

    session = _Session(user_id='test_user', token=str(supabase_key))
    test_client = create_client(str(supabase_url), str(supabase_key))

    async def main_test():
        print('[TEST] Starting run_react_rag test')
        async for chunk in run_react_rag(session, test_client, 'Hello RAG test', []):
            print(f'[TEST] Received chunk: {chunk}')
        print('[TEST] run_react_rag test completed')

    asyncio.run(main_test())