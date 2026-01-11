import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Embedding model name
EMBEDDING_MODEL = "text-embedding-3-small"  # or "text-embedding-ada-002"

def get_embeddings(text: str) -> list:
    """
    Generate embeddings for a given text using OpenAI's embedding model.
    
    Args:
        text: The text to generate embeddings for
        
    Returns:
        A list of floats representing the embedding vector
    """
    try:
        # Clean and prepare text
        text = text.strip()
        if not text:
            raise ValueError("Text cannot be empty")
        
        # Generate embedding
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        
        return response.data[0].embedding
    except Exception as e:
        raise Exception(f"Error generating embeddings: {str(e)}")


def get_embeddings_batch(texts: list) -> list:
    """
    Generate embeddings for multiple texts in batch.
    
    Args:
        texts: List of texts to generate embeddings for
        
    Returns:
        List of embedding vectors
    """
    try:
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts
        )
        
        return [item.embedding for item in response.data]
    except Exception as e:
        raise Exception(f"Error generating batch embeddings: {str(e)}")

