#!/usr/bin/env python3
"""
Debug script to check user document setup for evaluation.
This helps diagnose why evaluations are failing due to missing documents.
"""

import asyncio
import os
import sys
from supabase import create_client

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from evaluation.config import TEST_USER_EMAIL, TEST_USER_PASSWORD, SUPABASE_URL, SUPABASE_KEY
from api.v1.dependencies import Session

async def debug_user_documents():
    """Debug function to check user document setup."""
    
    print("=" * 60)
    print("🔍 DEBUGGING USER DOCUMENT SETUP")
    print("=" * 60)
    
    # Check configuration
    print(f"\n📋 Configuration:")
    print(f"  Test Email: {TEST_USER_EMAIL}")
    print(f"  Supabase URL: {SUPABASE_URL[:30]}..." if SUPABASE_URL else "Not set")
    print(f"  Has Password: {'Yes' if TEST_USER_PASSWORD else 'No'}")
    
    if not all([TEST_USER_EMAIL, TEST_USER_PASSWORD, SUPABASE_URL, SUPABASE_KEY]):
        print("\n❌ MISSING CONFIGURATION")
        print("Please check your .env file has:")
        print("  - TEST_EMAIL")
        print("  - TEST_PASSWORD") 
        print("  - SUPABASE_URL")
        print("  - SUPABASE_ANON_KEY")
        return
    
    # Authenticate
    print(f"\n🔐 Authenticating...")
    auth_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        response = await asyncio.to_thread(
            auth_client.auth.sign_in_with_password,
            {"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        
        if not response.session or not response.user:
            print("❌ Authentication failed")
            return
            
        user_id = response.user.id
        print(f"✅ Authenticated as user: {user_id}")
        
        # Set up authenticated client
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        client.options.headers["Authorization"] = f"Bearer {response.session.access_token}"
        
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return
    
    # Check documents
    print(f"\n📁 Checking documents...")
    try:
        docs_response = client.table('documents')\
            .select('id, filename, user_id, company_name, report_date, status')\
            .eq('user_id', user_id)\
            .execute()
        
        documents = docs_response.data
        print(f"  Found {len(documents)} documents for this user")
        
        if not documents:
            print("\n❌ NO DOCUMENTS FOUND!")
            
            # Check if documents exist for other users
            all_docs_response = client.table('documents')\
                .select('id, filename, user_id, company_name')\
                .limit(10)\
                .execute()
            
            print(f"\n📊 Sample documents in database (any user):")
            for doc in all_docs_response.data:
                print(f"  - {doc['filename']} (user: {doc['user_id'][:8]}...)")
            
            print(f"\n🔧 SOLUTIONS:")
            print(f"  1. Upload documents to user: {user_id}")
            print(f"  2. Change TEST_EMAIL to match user who has documents")
            print(f"  3. Copy documents from another user (if testing)")
            
        else:
            print(f"\n✅ Documents found:")
            for doc in documents:
                print(f"  - {doc['filename']}")
                print(f"    ID: {doc['id']}")
                print(f"    Date: {doc['report_date']}")
                print(f"    Status: {doc['status']}")
                print(f"    Company: {doc['company_name']}")
                print()
        
    except Exception as e:
        print(f"❌ Error checking documents: {e}")
        return
    
    # Check document chunks
    print(f"\n📄 Checking document chunks...")
    try:
        chunks_response = client.table('chunks')\
            .select('id, document_id, section_heading')\
            .eq('user_id', user_id)\
            .execute()
        
        chunks = chunks_response.data
        print(f"  Found {len(chunks)} chunks for this user")
        
        if not chunks:
            print("\n❌ NO CHUNKS FOUND!")
            print("  This means no searchable content is available")
            print("  Documents may not have been processed properly")
        else:
            print(f"\n✅ Sample chunks:")
            for chunk in chunks[:5]:
                print(f"  - {chunk['section_heading']}")
        
    except Exception as e:
        print(f"❌ Error checking chunks: {e}")
        chunks = []  # Set chunks to empty list on error
    
    # Test a simple retrieval
    if documents and chunks:
        print(f"\n🔍 Testing retrieval...")
        try:
            from src.llm.tools.FunctionCaller import RetrievalService
            from src.llm.OpenAIClient import OpenAIClient
            from src.storage.SupabaseService import SupabaseService
            
            retrieval = RetrievalService(
                openai_client=OpenAIClient(),
                supabase_service=SupabaseService(supabase_client=client),
                user_id=user_id
            )
            
            result = retrieval.retrieve_chunks("revenue October 2023", 3)
            print(f"✅ Retrieval test successful:")
            print(f"  Result length: {len(result)} characters")
            print(f"  Preview: {result[:200]}...")
            
        except Exception as e:
            print(f"❌ Retrieval test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 DEBUG COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(debug_user_documents())
