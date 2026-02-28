from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
import os
import asyncio
from datetime import datetime
import uuid

from Authentication.supabase_client import supabase, supabase_admin
from Services.embeddings import get_embeddings, get_embeddings_for_document
from Services.video_processor import process_video, extract_text_from_video, extract_video_chunks
from Services.retrieval import retrieve_relevant_documents
from Services.data_normalization import normalize_query, normalize_metadata, normalize_and_chunk_document

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
    Document text is normalized before processing.
    """
    try:
        # Normalize and chunk document if necessary
        chunks = normalize_and_chunk_document(document.text)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="Document text is empty after normalization")
        
        # Normalize metadata
        normalized_metadata = normalize_metadata(document.metadata)
        
        # Store each chunk as a separate document (or combine if single chunk)
        doc_ids = []
        for i, chunk in enumerate(chunks):
            # Generate embeddings for the chunk
            embedding = get_embeddings(chunk)
            
            # Create document record
            doc_id = str(uuid.uuid4())
            chunk_metadata = normalized_metadata.copy()
            if len(chunks) > 1:
                chunk_metadata["chunk_index"] = i
                chunk_metadata["total_chunks"] = len(chunks)
            
            document_data = {
                "id": doc_id,
                "text": chunk,
                "embedding": embedding,
                "metadata": chunk_metadata,
                "document_type": document.document_type,
                "user_id": user.user.id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Store in Supabase
            result = supabase_admin.table("documents").insert(document_data).execute()
            doc_ids.append(doc_id)
        
        return {
            "message": "Document stored successfully",
            "document_id": doc_ids[0] if len(doc_ids) == 1 else doc_ids,
            "chunks_created": len(chunks),
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing document: {str(e)}")


# Endpoint to upload and process video
@router.post("/documents/video")
async def upload_video(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    chunk_duration_sec: Optional[float] = Form(120.0),
    user = Depends(verify_token)
):
    """
    Upload a video file, split it into time-based chunks, transcribe each chunk,
    and store each chunk in the DB with embeddings and segment metadata.
    """
    video_path = None
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # Save video temporarily
        upload_id = str(uuid.uuid4())
        video_path = f"/tmp/{upload_id}_{file.filename}"
        
        content = await file.read()
        file_size = len(content)
        with open(video_path, "wb") as buffer:
            buffer.write(content)
        
        # Split video into time-based chunks and transcribe (run in thread pool to avoid blocking)
        loop = asyncio.get_event_loop()
        chunks = await loop.run_in_executor(
            None,
            lambda: extract_video_chunks(video_path, chunk_duration_sec=chunk_duration_sec or 120.0),
        )
        
        if not chunks:
            raise HTTPException(status_code=400, detail="Could not extract text from video")
        
        # Normalize metadata
        raw_metadata = {
            "title": title or file.filename,
            "description": description,
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size": file_size,
        }
        normalized_metadata = normalize_metadata(raw_metadata)
        
        # Optionally upload video to Supabase Storage (before loop so all chunks can reference it)
        try:
            storage_path = f"videos/{user.user.id}/{upload_id}_{file.filename}"
            supabase_admin.storage.from_("videos").upload(
                storage_path,
                content,
                file_options={"content-type": file.content_type}
            )
            normalized_metadata["storage_path"] = storage_path
        except Exception as storage_error:
            print(f"Storage upload failed: {str(storage_error)}")
        
        doc_ids = []
        for i, chunk_data in enumerate(chunks):
            chunk_text = chunk_data["text"]
            if not chunk_text or not chunk_text.strip():
                continue
            embedding = get_embeddings(chunk_text)
            chunk_id = str(uuid.uuid4())
            chunk_metadata = normalized_metadata.copy()
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(chunks)
            chunk_metadata["start_sec"] = chunk_data.get("start_sec")
            chunk_metadata["end_sec"] = chunk_data.get("end_sec")
            
            document_data = {
                "id": chunk_id,
                "text": chunk_text,
                "embedding": embedding,
                "metadata": chunk_metadata,
                "document_type": "video",
                "user_id": user.user.id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            supabase_admin.table("documents").insert(document_data).execute()
            doc_ids.append(chunk_id)
        
        primary_doc_id = doc_ids[0] if doc_ids else None
        
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
        
        full_transcription = " ".join(c["text"] for c in chunks).strip()
        return {
            "message": "Video processed and stored successfully",
            "document_id": primary_doc_id,
            "document_ids": doc_ids if len(doc_ids) > 1 else doc_ids,
            "chunks_created": len(doc_ids),
            "transcription_preview": full_transcription[:200] + "..." if len(full_transcription) > 200 else full_transcription,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except OSError:
                pass
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")


# Endpoint to retrieve relevant documents
@router.post("/retrieve")
async def retrieve_documents(
    query: QueryModel,
    user = Depends(verify_token)
):
    """
    Retrieve relevant documents based on a query using vector similarity search.
    Query is normalized before processing.
    """
    try:
        # Normalize query before processing
        normalized_query = normalize_query(query.query)
        
        # Get query embedding (normalization happens inside get_embeddings too)
        query_embedding = get_embeddings(normalized_query)
        
        # Retrieve relevant documents
        relevant_docs = await retrieve_relevant_documents(
            query_embedding=query_embedding,
            top_k=query.top_k,
            user_id=user.user.id
        )
        
        return {
            "query": query.query,
            "normalized_query": normalized_query,
            "results": relevant_docs,
            "count": len(relevant_docs)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
    Message is normalized before processing.
    """
    try:
        # Normalize chat message before processing
        normalized_message = normalize_query(chat.message)
        
        # Get query embedding (normalization happens inside get_embeddings too)
        query_embedding = get_embeddings(normalized_message)
        
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
                "normalized_message": normalized_message,
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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

