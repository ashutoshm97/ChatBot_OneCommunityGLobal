# Data Normalization Documentation

## Overview
All data passed to models (embeddings, video processing, retrieval) is now normalized before processing to ensure consistency, improve accuracy, and handle edge cases.

## Normalization Steps

### 1. Text Normalization (`normalize_text`)
Applied to all text inputs before processing:
- **Unicode Normalization**: Converts text to NFC (Normalized Form Canonical Composition)
- **Control Character Removal**: Removes null bytes and non-printable control characters
- **Whitespace Normalization**: 
  - Replaces multiple spaces with single space
  - Normalizes multiple newlines to paragraph breaks (double newline)
  - Trims leading/trailing whitespace from each line
- **Case Handling**: Optional lowercase conversion (preserved for embeddings to maintain semantic meaning)

### 2. Embedding-Specific Normalization (`normalize_for_embeddings`)
Applied before generating embeddings:
- All standard text normalization
- **Zero-Width Character Removal**: Removes invisible Unicode characters that can affect embeddings
- **Empty Text Validation**: Ensures text is not empty after normalization
- **Case Preservation**: Maintains original case for better semantic understanding

### 3. Query Normalization (`normalize_query`)
Applied to user queries before retrieval:
- Standard text normalization
- **Punctuation Handling**: Removes trailing question marks and periods while preserving semantic meaning
- **Empty Query Validation**: Ensures query is meaningful after normalization

### 4. Transcription Normalization (`normalize_transcription`)
Applied to video transcriptions:
- Standard text normalization
- **Punctuation Cleanup**: 
  - Removes excessive punctuation repetition (e.g., "!!!" → "!!")
  - Ensures proper spacing around punctuation marks
- **Formatting**: Improves readability of transcribed text

### 5. Document Chunking (`chunk_text` & `normalize_and_chunk_document`)
For large documents:
- **Automatic Chunking**: Splits documents exceeding 8000 characters into smaller chunks
- **Smart Boundaries**: Attempts to break at sentence boundaries for better context preservation
- **Overlap**: Includes 200 characters of overlap between chunks to maintain context
- **Chunk Size**: Default 5000 characters per chunk (configurable)

### 6. Video File Validation (`validate_video_file`)
Before video processing:
- **File Existence Check**: Verifies file exists and is readable
- **Size Validation**: Checks file size against maximum limit (default: 500 MB)
- **Format Validation**: Ensures file extension is in allowed formats list
- **Metadata Extraction**: Collects file size and extension information

### 7. Metadata Normalization (`normalize_metadata`)
Applied to all metadata dictionaries:
- **Key Normalization**: Converts keys to strings and trims whitespace
- **Value Normalization**: 
  - Strings: Normalized using text normalization
  - Lists: Each string item is normalized
  - Nested dictionaries: Recursively normalized
  - Other types: Preserved as-is
- **Empty Value Filtering**: Removes empty strings and empty lists

## Integration Points

### Embeddings Service
- `get_embeddings()`: Normalizes text before generating embeddings
- `get_embeddings_batch()`: Normalizes all texts in batch
- `get_embeddings_for_document()`: Normalizes and chunks large documents

### Video Processing Service
- `extract_text_from_video()`: Validates video file and normalizes transcription
- `process_video()`: Validates video and normalizes all output data

### Retrieval Service
- Queries are normalized before generating embeddings and searching

### RAG Routes
- **Document Storage**: Text is normalized and chunked if necessary
- **Video Upload**: Video is validated, transcription is normalized, and chunked if needed
- **Query/Retrieval**: Queries are normalized before processing
- **Chat**: Messages are normalized before retrieval and response generation
- **Metadata**: All metadata is normalized before storage

## Benefits

1. **Consistency**: All data follows the same format, improving search accuracy
2. **Quality**: Removes artifacts and formatting issues that could affect model performance
3. **Robustness**: Handles edge cases like empty text, special characters, and large documents
4. **Performance**: Chunking allows processing of large documents within model limits
5. **Accuracy**: Normalized queries match normalized documents more effectively

## Configuration

Normalization parameters can be adjusted in `Services/data_normalization.py`:
- `MAX_TEXT_LENGTH`: Maximum text length before chunking (default: 8000)
- `CHUNK_SIZE`: Size of each chunk (default: 5000)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 200)
- `max_size_mb`: Maximum video file size (default: 500 MB)
- `allowed_formats`: List of allowed video formats

## Example Flow

1. **User uploads document**: "  Hello   World!!!  "
2. **Normalization**: "Hello World!!"
3. **Embedding generation**: Uses normalized text
4. **Storage**: Normalized text stored in database

1. **User queries**: "What is machine learning???"
2. **Normalization**: "What is machine learning"
3. **Embedding generation**: Uses normalized query
4. **Retrieval**: Matches against normalized documents

## Error Handling

- Empty text after normalization raises `ValueError`
- Invalid video files raise `ValueError` with specific error messages
- All normalization errors are caught and wrapped with descriptive messages

