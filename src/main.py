import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

# Global Supabase client initialization
supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase client initialized successfully globally.")
    except Exception as e:
        print(f"⚠️ Global Supabase client initialization failed: {e}")
        supabase = None # Ensure supabase is None if initialization fails
else:
    print("⚠️ Supabase URL or Key not found in environment. Supabase client not initialized.")
    # exit("Error: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file") # Optionally, make it strict

class Document(BaseModel):
    id: str
    filename: str
    user_id: str

class Session(BaseModel):
    user_id: str
    token: str

app = FastAPI(title="Backend API with Supabase Auth", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_session(token: str = Depends(oauth2_scheme)) -> Session:
    if not token:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        # Use the global supabase client if available, or create a new one if necessary for this function.
        # However, for auth, it's typical to use a fresh client or ensure the global one is valid.
        # For simplicity here, we'll re-create one for the auth context if not globally available or if preferred.
        current_supabase_client: Client
        if SUPABASE_URL and SUPABASE_KEY: # Ensure credentials exist before trying to create a client
            current_supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        else:
            # This case should ideally be handled by application startup checks
            # or the global client initialization failure.
            print("Backend: Error validating token - Supabase credentials not available.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server configuration error regarding Supabase credentials.",
            )

        res = current_supabase_client.auth.get_user(jwt=token)
        user = res.user
        if not user or not user.id:
            raise ValueError("Invalid user")
        print(f"Backend: Token validated for user {user.id}")
        return Session(user_id=user.id, token=token)
    except Exception as e:
        print(f"Backend: Error validating token: {e}")
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/documents", response_model=List[Document], summary="Get documents for the authenticated user")
async def list_documents(session: Session = Depends(get_session)):
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("Backend: Error fetching documents - Supabase credentials not configured.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server configuration error for Supabase.",
            )

        # Create a new Supabase client instance for this request, configured with the user's JWT
        authed_supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Manually set the Authorization header for this client instance.
        # This ensures that PostgREST requests made by this client instance are authenticated as the user.
        authed_supabase_client.options.headers["Authorization"] = f"Bearer {session.token}"
        # The 'apikey' header (SUPABASE_KEY) is already set by create_client for general API access.

        # Use the authenticated Supabase client to fetch documents
        resp = authed_supabase_client.table("documents").select("id, filename, user_id").eq("user_id", session.user_id).execute()
        
        docs = resp.data or []
        print(f"Backend: Fetched {len(docs)} documents for user {session.user_id} using user's token.")
        for d in docs:
            print(f"  - Doc ID: {d['id']}, Filename: {d['filename']}")
        return [Document(**d) for d in docs]
    except Exception as e:
        print(f"Backend: Error fetching documents: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc() # Log full traceback to server logs
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch documents. Error: {type(e).__name__}", # Provide error type to client
        )

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "AI CFO API is operational",
        "supabase_status": "connected" if supabase else "disconnected" # Now accurately reflects global client
    }


if __name__ == "__main__":
    import uvicorn # Ensure uvicorn import is here
    uvicorn.run(app, host="0.0.0.0", port=8000)



