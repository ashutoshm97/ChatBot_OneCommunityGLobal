from typing import List, Dict, Optional
from Authentication.supabase_client import supabase_admin
from Services.data_normalization import normalize_query
import math

async def retrieve_relevant_documents(
    query_embedding: List[float],
    top_k: int = 5,
    user_id: Optional[str] = None,
    similarity_threshold: float = 0.7
) -> List[Dict]:
    """
    Retrieve relevant documents using vector similarity search.
    
    Args:
        query_embedding: The embedding vector of the query
        top_k: Number of top results to return
        user_id: Optional user ID to filter documents
        similarity_threshold: Minimum similarity score (0-1)
        
    Returns:
        List of relevant documents with similarity scores
    """
    try:
        # Build the query
        # Note: This assumes you have a 'documents' table with an 'embedding' column of type vector
        # Supabase uses pgvector extension for vector operations
        
        # For Supabase with pgvector, we use cosine similarity
        # The query uses the <=> operator for cosine distance (1 - cosine similarity)
        
        # First, get all documents (or filter by user_id)
        query = supabase_admin.table("documents").select("*")
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        # Execute query to get all documents
        # Note: Supabase doesn't have built-in vector similarity search in the Python client
        # We'll need to use a raw SQL query or RPC function
        # For now, we'll fetch and compute similarity in Python (not ideal for large datasets)
        
        result = query.execute()
        documents = result.data
        
        if not documents:
            return []
        
        # Calculate cosine similarity for each document
        scored_docs = []
        for doc in documents:
            if "embedding" not in doc or doc["embedding"] is None:
                continue
            
            doc_embedding = doc["embedding"]
            
            # Calculate cosine similarity
            similarity = cosine_similarity(query_embedding, doc_embedding)
            
            if similarity >= similarity_threshold:
                scored_docs.append({
                    "id": doc["id"],
                    "text": doc.get("text", ""),
                    "metadata": doc.get("metadata", {}),
                    "document_type": doc.get("document_type", "text"),
                    "similarity": similarity,
                    "created_at": doc.get("created_at")
                })
        
        # Sort by similarity (descending) and return top_k
        scored_docs.sort(key=lambda x: x["similarity"], reverse=True)
        
        return scored_docs[:top_k]
    
    except Exception as e:
        raise Exception(f"Error retrieving documents: {str(e)}")


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score (0-1)
    """
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have the same length")
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(a * a for a in vec2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)


# Alternative: Use Supabase RPC function for vector search (more efficient)
async def retrieve_relevant_documents_rpc(
    query_embedding: List[float],
    top_k: int = 5,
    user_id: Optional[str] = None
) -> List[Dict]:
    """
    Retrieve relevant documents using a Supabase RPC function.
    This is more efficient for large datasets.
    
    Note: You need to create this RPC function in your Supabase database:
    
    CREATE OR REPLACE FUNCTION match_documents(
        query_embedding vector(1536),
        match_threshold float,
        match_count int,
        user_filter uuid
    )
    RETURNS TABLE (
        id uuid,
        text text,
        metadata jsonb,
        document_type text,
        similarity float
    )
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RETURN QUERY
        SELECT
            documents.id,
            documents.text,
            documents.metadata,
            documents.document_type,
            1 - (documents.embedding <=> query_embedding) as similarity
        FROM documents
        WHERE 
            (user_filter IS NULL OR documents.user_id = user_filter)
            AND (1 - (documents.embedding <=> query_embedding)) > match_threshold
        ORDER BY documents.embedding <=> query_embedding
        LIMIT match_count;
    END;
    $$;
    """
    try:
        result = supabase_admin.rpc(
            "match_documents",
            {
                "query_embedding": query_embedding,
                "match_threshold": 0.7,
                "match_count": top_k,
                "user_filter": user_id
            }
        ).execute()
        
        return result.data if result.data else []
    except Exception as e:
        # Fallback to Python-based retrieval if RPC fails
        return await retrieve_relevant_documents(query_embedding, top_k, user_id)

