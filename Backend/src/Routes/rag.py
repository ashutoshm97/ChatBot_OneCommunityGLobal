from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
import os
from datetime import datetime
import uuid

from Authentication.supabase_client import supabase, supabase_admin
from Services.embeddings import get_embeddings
from Services.video_processor import process_video, extract_text_from_video
from Services.retrieval import retrieve_relevant_documents

router = APIRouter(prefix="/rag", tags=["rag"])

security = HTTPBearer()

# Pydantic models
class DocumentModel(BaseModel):
    text: str
    metadata: Optional[dict] = None
    document_type: Optional[str] = "text"

class QueryModel(BaseModel):
    query: str
    top_k: Optional[int] = 5

class ChatModel(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    top_k: Optional[int] = 5

class VideoUploadModel(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

# Dependency to verify authentication
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        # Verify the token with Supabase
        user = supabase.auth.get_user(credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")


# Endpoint to store text documents
@router.post("/documents")
async def store_document(
    document: DocumentModel,
    user = Depends(verify_token)
):
    """
    Store a text document in the database with embeddings.
    """
    try:
        # Generate embeddings for the document
        embedding = get_embeddings(document.text)
        
        # Create document record
        doc_id = str(uuid.uuid4())
        document_data = {
            "id": doc_id,
            "text": document.text,
            "embedding": embedding,
            "metadata": document.metadata or {},
            "document_type": document.document_type,
            "user_id": user.user.id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Store in Supabase (assuming you have a 'documents' table with vector column)
        result = supabase_admin.table("documents").insert(document_data).execute()
        
        return {
            "message": "Document stored successfully",
            "document_id": doc_id,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing document: {str(e)}")


# Endpoint to upload and process video
@router.post("/documents/video")
async def upload_video(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    user = Depends(verify_token)
):
    """
    Upload a video file, extract text (transcription), and store with embeddings.
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # Save video temporarily
        video_id = str(uuid.uuid4())
        video_path = f"/tmp/{video_id}_{file.filename}"
        
        with open(video_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract text from video (transcription)
        transcription = await extract_text_from_video(video_path)
        
        if not transcription or len(transcription.strip()) == 0:
            raise HTTPException(status_code=400, detail="Could not extract text from video")
        
        # Generate embeddings for the transcription
        embedding = get_embeddings(transcription)
        
        # Store video metadata and transcription
        document_data = {
            "id": video_id,
            "text": transcription,
            "embedding": embedding,
            "metadata": {
                "title": title or file.filename,
                "description": description,
                "filename": file.filename,
                "content_type": file.content_type,
                "file_size": len(content)
            },
            "document_type": "video",
            "user_id": user.user.id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Store in Supabase
        result = supabase_admin.table("documents").insert(document_data).execute()
        
        # Optionally store video file in Supabase Storage
        try:
            # Upload video to Supabase Storage
            storage_path = f"videos/{user.user.id}/{video_id}_{file.filename}"
            supabase_admin.storage.from_("videos").upload(
                storage_path,
                content,
                file_options={"content-type": file.content_type}
            )
            document_data["metadata"]["storage_path"] = storage_path
        except Exception as storage_error:
            # Log but don't fail if storage upload fails
            print(f"Storage upload failed: {str(storage_error)}")
        
        # Clean up temporary file
        if os.path.exists(video_path):
            os.remove(video_path)
        
        return {
            "message": "Video processed and stored successfully",
            "document_id": video_id,
            "transcription": transcription[:200] + "..." if len(transcription) > 200 else transcription,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if 'video_path' in locals() and os.path.exists(video_path):
            os.remove(video_path)
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")


# Endpoint to retrieve relevant documents
@router.post("/retrieve")
async def retrieve_documents(
    query: QueryModel,
    user = Depends(verify_token)
):
    """
    Retrieve relevant documents based on a query using vector similarity search.
    """
    try:
        # Get query embedding
        query_embedding = get_embeddings(query.query)
        
        # Retrieve relevant documents
        relevant_docs = await retrieve_relevant_documents(
            query_embedding=query_embedding,
            top_k=query.top_k,
            user_id=user.user.id
        )
        
        return {
            "query": query.query,
            "results": relevant_docs,
            "count": len(relevant_docs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")


# Endpoint for RAG-based chat
@router.post("/chat")
async def rag_chat(
    chat: ChatModel,
    user = Depends(verify_token)
):
    """
    Chat endpoint that uses RAG to retrieve relevant context and generate responses.
    """
    try:
        # Get query embedding
        query_embedding = get_embeddings(chat.message)
        
        # Retrieve relevant documents
        relevant_docs = await retrieve_relevant_documents(
            query_embedding=query_embedding,
            top_k=chat.top_k,
            user_id=user.user.id
        )
        
        # Build context from retrieved documents
        context = "\n\n".join([doc.get("text", "") for doc in relevant_docs])
        
        # Here you would typically call an LLM (like OpenAI GPT) with the context
        # For now, we'll return the context and relevant documents
        # You can integrate with OpenAI, Anthropic, or other LLM providers
        
        response_text = f"Based on the retrieved context, here are the relevant documents:\n\n{context[:1000]}..."
        
        # Store conversation in database if conversation_id is provided
        if chat.conversation_id:
            conversation_data = {
                "conversation_id": chat.conversation_id,
                "user_id": user.user.id,
                "message": chat.message,
                "response": response_text,
                "retrieved_docs": [doc.get("id") for doc in relevant_docs],
                "created_at": datetime.utcnow().isoformat()
            }
            try:
                supabase_admin.table("conversations").insert(conversation_data).execute()
            except Exception as e:
                print(f"Error storing conversation: {str(e)}")
        
        return {
            "response": response_text,
            "relevant_documents": relevant_docs,
            "conversation_id": chat.conversation_id,
            "retrieved_count": len(relevant_docs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")


# Endpoint to get all documents for a user
@router.get("/documents")
async def get_documents(
    skip: int = 0,
    limit: int = 20,
    document_type: Optional[str] = None,
    user = Depends(verify_token)
):
    """
    Get all documents for the authenticated user.
    """
    try:
        query = supabase.table("documents").select("*").eq("user_id", user.user.id)
        
        if document_type:
            query = query.eq("document_type", document_type)
        
        result = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
        
        # Remove embeddings from response for efficiency
        documents = result.data
        for doc in documents:
            if "embedding" in doc:
                del doc["embedding"]
        
        return {
            "documents": documents,
            "count": len(documents),
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")


# Endpoint to delete a document
@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    user = Depends(verify_token)
):
    """
    Delete a document by ID.
    """
    try:
        # Verify ownership
        result = supabase.table("documents").select("user_id").eq("id", document_id).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if result.data[0]["user_id"] != user.user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this document")
        
        # Delete document
        supabase_admin.table("documents").delete().eq("id", document_id).execute()
        
        return {
            "message": "Document deleted successfully",
            "document_id": document_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

