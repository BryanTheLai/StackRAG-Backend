import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL") or exit("Error: SUPABASE_URL must be set")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or exit("Error: SUPABASE_ANON_KEY must be set")


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
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
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
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        res = supabase.auth.get_user(jwt=token)
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
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        supabase.auth.set_session(session.token, "")
        resp = supabase.table("documents").select("id, filename, user_id").execute()
        docs = resp.data or []
        print(f"Backend: Fetched {len(docs)} documents for user {session.user_id}")
        for d in docs:
            print(f"  - Doc ID: {d['id']}, Filename: {d['filename']}")
        return [Document(**d) for d in docs]
    except Exception as e:
        print(f"Backend: Error fetching documents: {e}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch documents",
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)