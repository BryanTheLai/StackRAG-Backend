from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from api import router as api_router

load_dotenv()  # Load environment variables once for dependencies

app = FastAPI(title="Backend API with Supabase Auth", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", 
                   "http://localhost:5174","https://frontend-ai-cfo.vercel.app",
                   "https://www.stackifier.com"
                   ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "AI CFO API is operational"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)



