import re
import unicodedata
from typing import Optional, List
import os

# Maximum token length for OpenAI embeddings (text-embedding-3-small supports up to 8191 tokens)
# Using a conservative limit of 8000 tokens, which is approximately 6000-8000 words
MAX_TEXT_LENGTH = 8000  # characters (rough estimate, actual token count may vary)
CHUNK_SIZE = 5000  # characters per chunk for large documents
CHUNK_OVERLAP = 200  # characters overlap between chunks

def normalize_text(text: str, lower_case: bool = False, remove_extra_whitespace: bool = True) -> str:
    """
    Normalize text data before processing.
    
    Args:
        text: Input text to normalize
        lower_case: Whether to convert to lowercase
        remove_extra_whitespace: Whether to remove extra whitespace
        
    Returns:
        Normalized text
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove null bytes and control characters (except newlines and tabs)
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
    
    # Normalize unicode (NFD to NFC normalization)
    text = unicodedata.normalize('NFC', text)
    
    # Remove extra whitespace
    if remove_extra_whitespace:
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        # Replace multiple newlines with double newline (paragraph break)
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove leading/trailing whitespace from each line
        text = '\n'.join(line.strip() for line in text.split('\n'))
    
    # Convert to lowercase if requested
    if lower_case:
        text = text.lower()
    
    # Strip leading and trailing whitespace
    text = text.strip()
    
    return text


def normalize_for_embeddings(text: str) -> str:
    """
    Normalize text specifically for embedding generation.
    Preserves case and structure but cleans the text.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized text ready for embeddings
    """
    # Normalize text (preserve case for better semantic understanding)
    normalized = normalize_text(text, lower_case=False, remove_extra_whitespace=True)
    
    # Remove or replace problematic characters that might affect embeddings
    # Keep punctuation as it can be semantically important
    # Remove zero-width characters
    normalized = re.sub(r'[\u200B-\u200D\uFEFF]', '', normalized)
    
    # Ensure text is not empty
    if not normalized or len(normalized.strip()) == 0:
        raise ValueError("Text cannot be empty after normalization")
    
    return normalized


def normalize_query(query: str) -> str:
    """
    Normalize user query for retrieval.
    
    Args:
        query: User query string
        
    Returns:
        Normalized query
    """
    if not query or not isinstance(query, str):
        raise ValueError("Query cannot be empty")
    
    # Normalize text
    normalized = normalize_text(query, lower_case=False, remove_extra_whitespace=True)
    
    # Remove trailing question marks and periods (keep for semantic meaning)
    # But ensure it's not just punctuation
    normalized = normalized.strip('?.,!;:')
    
    if not normalized or len(normalized.strip()) == 0:
        raise ValueError("Query cannot be empty after normalization")
    
    return normalized


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split large text into chunks with overlap for better context preservation.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # If not the last chunk, try to break at a sentence boundary
        if end < len(text):
            # Look for sentence endings within the last 200 characters
            search_start = max(start, end - 200)
            sentence_end = max(
                text.rfind('.', search_start, end),
                text.rfind('!', search_start, end),
                text.rfind('?', search_start, end),
                text.rfind('\n', search_start, end)
            )
            
            if sentence_end > search_start:
                end = sentence_end + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks


def normalize_and_chunk_document(text: str, max_length: int = MAX_TEXT_LENGTH) -> List[str]:
    """
    Normalize a document and chunk it if necessary.
    
    Args:
        text: Document text
        max_length: Maximum length before chunking
        
    Returns:
        List of normalized text chunks
    """
    # Normalize the text
    normalized = normalize_for_embeddings(text)
    
    # If text is within limits, return as single chunk
    if len(normalized) <= max_length:
        return [normalized]
    
    # Otherwise, chunk it
    return chunk_text(normalized)


def normalize_transcription(transcription: str) -> str:
    """
    Normalize video transcription text.
    Handles common transcription artifacts and formatting.
    
    Args:
        transcription: Raw transcription text
        
    Returns:
        Normalized transcription
    """
    if not transcription:
        return ""
    
    # Normalize text
    normalized = normalize_text(transcription, lower_case=False, remove_extra_whitespace=True)
    
    # Remove common transcription artifacts
    # Remove filler words patterns (optional, can be customized)
    # normalized = re.sub(r'\b(um|uh|er|ah)\b', '', normalized, flags=re.IGNORECASE)
    
    # Remove excessive punctuation repetition
    normalized = re.sub(r'([.!?]){3,}', r'\1\1', normalized)
    
    # Ensure proper spacing around punctuation
    normalized = re.sub(r'\s+([,.!?;:])', r'\1', normalized)
    normalized = re.sub(r'([,.!?;:])\s*([,.!?;:])', r'\1 \2', normalized)
    
    return normalized.strip()


def validate_video_file(file_path: str, max_size_mb: int = 500, allowed_formats: List[str] = None) -> dict:
    """
    Validate and normalize video file metadata.
    
    Args:
        file_path: Path to video file
        max_size_mb: Maximum file size in MB
        allowed_formats: List of allowed video formats (extensions)
        
    Returns:
        Dictionary with validation results and normalized metadata
    """
    if allowed_formats is None:
        allowed_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v']
    
    validation_result = {
        "valid": False,
        "errors": [],
        "metadata": {}
    }
    
    # Check if file exists
    if not os.path.exists(file_path):
        validation_result["errors"].append("File does not exist")
        return validation_result
    
    # Check file size
    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / (1024 * 1024)
    validation_result["metadata"]["size_bytes"] = file_size
    validation_result["metadata"]["size_mb"] = round(file_size_mb, 2)
    
    if file_size_mb > max_size_mb:
        validation_result["errors"].append(f"File size ({file_size_mb:.2f} MB) exceeds maximum ({max_size_mb} MB)")
        return validation_result
    
    # Check file extension
    file_ext = os.path.splitext(file_path)[1].lower()
    validation_result["metadata"]["extension"] = file_ext
    
    if file_ext not in allowed_formats:
        validation_result["errors"].append(f"File format {file_ext} not allowed. Allowed formats: {', '.join(allowed_formats)}")
        return validation_result
    
    # Check if file is readable
    if not os.access(file_path, os.R_OK):
        validation_result["errors"].append("File is not readable")
        return validation_result
    
    validation_result["valid"] = True
    return validation_result


def normalize_metadata(metadata: Optional[dict]) -> dict:
    """
    Normalize and clean metadata dictionary.
    
    Args:
        metadata: Metadata dictionary
        
    Returns:
        Normalized metadata dictionary
    """
    if not metadata:
        return {}
    
    if not isinstance(metadata, dict):
        return {}
    
    normalized = {}
    
    for key, value in metadata.items():
        # Normalize key (remove special characters, convert to string)
        normalized_key = str(key).strip()
        if not normalized_key:
            continue
        
        # Normalize value based on type
        if isinstance(value, str):
            normalized_value = normalize_text(value, lower_case=False, remove_extra_whitespace=True)
            if normalized_value:
                normalized[normalized_key] = normalized_value
        elif isinstance(value, (int, float, bool)):
            normalized[normalized_key] = value
        elif isinstance(value, dict):
            normalized[normalized_key] = normalize_metadata(value)
        elif isinstance(value, list):
            # Normalize list items
            normalized_list = []
            for item in value:
                if isinstance(item, str):
                    normalized_item = normalize_text(item, lower_case=False, remove_extra_whitespace=True)
                    if normalized_item:
                        normalized_list.append(normalized_item)
                else:
                    normalized_list.append(item)
            if normalized_list:
                normalized[normalized_key] = normalized_list
        else:
            normalized[normalized_key] = value
    
    return normalized

