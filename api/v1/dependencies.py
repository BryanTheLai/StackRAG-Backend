import os

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from supabase import create_client

# Environment configuration
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")

# Authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

class Session(BaseModel):
    user_id: str
    token: str


async def get_session(token: str = Depends(oauth2_scheme)) -> Session:
    """Validate JWT token and return user session."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Auth-only ad-hoc Supabase client, not reused across requests
        auth_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        auth_client.options.headers["Authorization"] = f"Bearer {token}"
        response = auth_client.auth.get_user(jwt=token)
        
        if not response.user or not response.user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return Session(user_id=response.user.id, token=token)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token",
            headers={"WWW-Authenticate": "Bearer"},
        )
