import os
import sys
import asyncio
from supabase import create_client

# Add project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from evaluation.config import TEST_USER_EMAIL, TEST_USER_PASSWORD, SUPABASE_URL, SUPABASE_KEY

async def quick_check():
    print("Quick check for chunks...")
    
    # Auth
    auth_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = await asyncio.to_thread(
        auth_client.auth.sign_in_with_password,
        {"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    )
    
    user_id = response.user.id
    print(f"User ID: {user_id}")
    
    # Set up client
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    client.options.headers["Authorization"] = f"Bearer {response.session.access_token}"
    
    # Check chunks
    try:
        chunks_response = client.table('chunks')\
            .select('id')\
            .eq('user_id', user_id)\
            .limit(5)\
            .execute()
        
        print(f"Chunks found: {len(chunks_response.data)}")
        
        if chunks_response.data:
            print("✅ You have chunks! The retrieval should work.")
            
            # Test a simple search
            from src.llm.tools.FunctionCaller import RetrievalService
            from src.llm.OpenAIClient import OpenAIClient
            from src.storage.SupabaseService import SupabaseService
            
            retrieval = RetrievalService(
                openai_client=OpenAIClient(),
                supabase_service=SupabaseService(supabase_client=client),
                user_id=user_id
            )
            
            result = await retrieval.retrieve_chunks("revenue October 2023", 3)
            print(f"Test retrieval result length: {len(result)}")
            
        else:
            print("❌ NO CHUNKS FOUND!")
            print("Your documents exist but haven't been processed into searchable chunks.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(quick_check())
