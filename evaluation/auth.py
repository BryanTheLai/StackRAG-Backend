# evaluation/auth.py
"""
Authentication utilities for RAG evaluation.
"""
import asyncio
from supabase import create_client
from api.v1.dependencies import Session
from config import TEST_USER_EMAIL, TEST_USER_PASSWORD, SUPABASE_URL, SUPABASE_KEY


async def setup_auth() -> tuple[Session, any]:
    """Setup authenticated session for evaluation."""
    print("🔐 Setting up authentication...")
    
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    response = await asyncio.to_thread(
        client.auth.sign_in_with_password,
        {"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    )
    
    session = Session(
        user_id=response.user.id, 
        token=response.session.access_token
    )
    
    client.options.headers["Authorization"] = f"Bearer {session.token}"
    
    print(f"✅ Authenticated as user: {session.user_id[:8]}...")
    
    return session, client
