# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Routes import auth, rag

app = FastAPI(
    title="RAG Chatbot API",
    description="API for RAG-based chatbot with document storage, retrieval, and video processing",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
