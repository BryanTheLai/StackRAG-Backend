import os
from supabase import create_client
from src.llm.OpenAIClient import OpenAIClient
from src.llm.tools.ChunkRetriever import RetrievalService
from src.storage.SupabaseService import SupabaseService

def _supabase_setup():
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in your .env file.")
    auth_client_local = create_client(supabase_url, supabase_key)

    retrieval_service_main = RetrievalService(
        openai_client = OpenAIClient(),
        supabase_service = SupabaseService(supabase_client=auth_client_local)
    )
    return retrieval_service_main

def call_function(function_call, functions, user_supabase_id):
    # actually call the setup function
    retrieval_service_main = _supabase_setup()      # ← add () here
    function_name = function_call.name
    function_args = function_call.args

    # 1. special case for your Retriever
    if function_name == "retrieve_financial_chunks":
        return retrieval_service_main.retrieve_chunks(
            user_id=user_supabase_id,
            **function_args
        )

    # 2. other tools
    for func in functions:
        if func.__name__ == function_name:
            return func(**function_args)

    # 3. not found
    return f"Function {function_name} not found in the provided functions."