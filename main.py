import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Annotated, List, Dict

from supabase import create_client, Client

load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("Error: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env")
    exit(1)

class DocumentInfo(BaseModel):
    filename: str
    id: str
    user_id: str

class UserSession(BaseModel):
    user_id: str
    token: str

app = FastAPI(
    title="Backend API with Supabase Auth",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_user_session(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> UserSession:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    temp_anon_client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    try:
        user_response = temp_anon_client.auth.get_user(jwt=token)
        if not user_response.user or not user_response.user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token or user session with Supabase (user not found)",
                headers={"WWW-Authenticate": "Bearer"},
            )
        print(f"Backend: Token successfully validated for user: {user_response.user.id}")
        return UserSession(user_id=str(user_response.user.id), token=token)
    except Exception as e:
        print(f"Backend: Error validating token with Supabase: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate token with Supabase: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get(
    "/documents",
    summary="Get documents for the authenticated user",
    response_model=List[DocumentInfo],
)
async def get_user_documents(
    session: Annotated[UserSession, Depends(get_current_user_session)]
):
    try:
        user_specific_client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        user_specific_client.auth.set_session(session.token, "")
        response = (
            user_specific_client.table("documents")
            .select("filename, id, user_id")
            .execute()
        )
        if response.data is None:
             print(f"Backend: No documents found or error for user {session.user_id}. Response: {response}")
             return []
        print(f"Backend: Fetched documents for user {session.user_id}. Count: {len(response.data)}")
        for doc_data in response.data:
            print(f"  - Doc ID: {doc_data['id']}, Filename: {doc_data['filename']}, User ID from DB: {doc_data['user_id']}")
        return [DocumentInfo(**doc_data) for doc_data in response.data]
    except Exception as e:
        print(f"Backend: Error fetching documents from Supabase: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch documents: {str(e)}",
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)