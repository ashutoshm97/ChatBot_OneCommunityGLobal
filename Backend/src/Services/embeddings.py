import os
from typing import Tuple
from openai import OpenAI
from dotenv import load_dotenv
from Services.data_normalization import normalize_for_embeddings, normalize_and_chunk_document

load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Embedding model name
EMBEDDING_MODEL = "text-embedding-3-small"  # or "text-embedding-ada-002"

def get_embeddings(text: str) -> list:
    """
    Generate embeddings for a given text using OpenAI's embedding model.
    Text is normalized before generating embeddings.
    
    Args:
        text: The text to generate embeddings for
        
    Returns:
        A list of floats representing the embedding vector
    """
    try:
        # Normalize text before generating embeddings
        normalized_text = normalize_for_embeddings(text)
        
        # Generate embedding
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=normalized_text
        )
        
        return response.data[0].embedding
    except Exception as e:
        raise Exception(f"Error generating embeddings: {str(e)}")


def get_embeddings_batch(texts: list) -> list:
    """
    Generate embeddings for multiple texts in batch.
    All texts are normalized before generating embeddings.
    
    Args:
        texts: List of texts to generate embeddings for
        
    Returns:
        List of embedding vectors
    """
    try:
        # Normalize all texts
        normalized_texts = [normalize_for_embeddings(text) for text in texts]
        
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=normalized_texts
        )
        
        return [item.embedding for item in response.data]
    except Exception as e:
        raise Exception(f"Error generating batch embeddings: {str(e)}")


def get_embeddings_for_document(text: str) -> Tuple[list, list]:
    """
    Generate embeddings for a document, handling chunking if necessary.
    
    Args:
        text: Document text (may be long)
        
    Returns:
        Tuple of (list of embeddings, list of chunk texts)
    """
    try:
        # Normalize and chunk the document
        chunks = normalize_and_chunk_document(text)
        
        if not chunks:
            raise ValueError("No valid text chunks after normalization")
        
        # Generate embeddings for all chunks
        embeddings = get_embeddings_batch(chunks)
        
        return embeddings, chunks
    except Exception as e:
        raise Exception(f"Error generating document embeddings: {str(e)}")

