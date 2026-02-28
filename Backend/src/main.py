# main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Routes import auth, rag

app = FastAPI(
    title="RAG Chatbot API",
    description="API for RAG-based chatbot with document storage, retrieval, and video processing",
    version="1.0.0"
)

# CORS: use explicit origins when credentials are needed (browsers reject allow_origins=["*"] with credentials)
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").strip()
cors_origins = [o.strip() for o in _cors_origins.split(",") if o.strip()] if _cors_origins else ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(rag.router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "RAG Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/auth",
            "rag": "/rag"
        }
    }
