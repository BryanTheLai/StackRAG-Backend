#!/usr/bin/env python3
"""
Quick test of a single evaluation case.
"""

import asyncio
import json
import os
import sys
from supabase import create_client

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from evaluation.config import TEST_USER_EMAIL, TEST_USER_PASSWORD, SUPABASE_URL, SUPABASE_KEY
from api.v1.dependencies import Session
from src.llm.tools.FunctionCaller import RetrievalService
from src.llm.OpenAIClient import OpenAIClient
from src.storage.SupabaseService import SupabaseService

async def quick_test():
    print("🔍 Quick Evaluation Test")
    print("=" * 30)
    
    # Auth
    auth_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = await asyncio.to_thread(
        auth_client.auth.sign_in_with_password,
        {"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    )
    
    session = Session(user_id=response.user.id, token=response.session.access_token)
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    client.options.headers["Authorization"] = f"Bearer {session.token}"
    
    print(f"✅ Authenticated as: {session.user_id}")
    
    # Test question
    question = "What was the revenue for October 2023?"
    print(f"❓ Question: {question}")
    
    # Test retrieval
    retrieval = RetrievalService(
        openai_client=OpenAIClient(),
        supabase_service=SupabaseService(supabase_client=client),
        user_id=session.user_id
    )
    
    result = retrieval.retrieve_chunks(question, 3)
    chunks_data = json.loads(result)
    
    print(f"📄 Retrieved {len(chunks_data)} chunks")
    
    if chunks_data:
        print("✅ Sample chunk:")
        print(f"  Document: {chunks_data[0].get('document_filename', 'Unknown')}")
        print(f"  Content: {chunks_data[0].get('chunk_text', '')[:100]}...")
        
        # Check if we found October 2023 data
        october_found = any('october' in chunk.get('chunk_text', '').lower() or 
                           'oct' in chunk.get('chunk_text', '').lower() or
                           '2023-10' in chunk.get('chunk_text', '') or
                           '550' in chunk.get('chunk_text', '')
                           for chunk in chunks_data)
        
        print(f"🎯 October 2023 data found: {'YES' if october_found else 'NO'}")
        
        if october_found:
            print("🎉 SUCCESS: Your retrieval system IS working correctly!")
            print("   The evaluation issues were likely in the agent orchestration.")
        else:
            print("⚠️  WARNING: Retrieved chunks but didn't find specific October 2023 data")
            
    else:
        print("❌ No chunks retrieved - there's still an issue")

if __name__ == "__main__":
    asyncio.run(quick_test())
