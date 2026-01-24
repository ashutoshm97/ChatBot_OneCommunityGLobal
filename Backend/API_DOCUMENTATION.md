# RAG Chatbot API Documentation

## Overview
This API provides endpoints for a RAG (Retrieval-Augmented Generation) based chatbot system. It supports storing documents (text and video), retrieving relevant documents using vector similarity search, and generating responses based on retrieved context.

## Base URL
```
http://localhost:8000
```

## Authentication
All RAG endpoints require authentication. Include the Bearer token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

## Endpoints

### 1. Store Text Document
**POST** `/rag/documents`

Store a text document with embeddings in the database.

**Request Body:**
```json
{
  "text": "Your document text here...",
  "metadata": {
    "title": "Document Title",
    "source": "example.com"
  },
  "document_type": "text"
}
```

**Response:**
```json
{
  "message": "Document stored successfully",
  "document_id": "uuid-here",
  "status": "success"
}
```

---

### 2. Upload and Process Video
**POST** `/rag/documents/video`

Upload a video file, extract transcription using Whisper, and store with embeddings.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:
  - `file`: Video file (required)
  - `title`: Optional title (form field)
  - `description`: Optional description (form field)

**Response:**
```json
{
  "message": "Video processed and stored successfully",
  "document_id": "uuid-here",
  "transcription": "Transcribed text preview...",
  "status": "success"
}
```

**Example (cURL):**
```bash
curl -X POST "http://localhost:8000/rag/documents/video" \
  -H "Authorization: Bearer <token>" \
  -F "file=@video.mp4" \
  -F "title=My Video" \
  -F "description=Video description"
```

---

### 3. Retrieve Relevant Documents
**POST** `/rag/retrieve`

Retrieve documents similar to a query using vector similarity search.

**Request Body:**
```json
{
  "query": "What is machine learning?",
  "top_k": 5
}
```

**Response:**
```json
{
  "query": "What is machine learning?",
  "results": [
    {
      "id": "uuid",
      "text": "Document text...",
      "metadata": {},
      "document_type": "text",
      "similarity": 0.85,
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "count": 1
}
```

---

### 4. RAG Chat
**POST** `/rag/chat`

Chat endpoint that retrieves relevant context and generates a response.

**Request Body:**
```json
{
  "message": "What is the main topic?",
  "conversation_id": "optional-conversation-id",
  "top_k": 5
}
```

**Response:**
```json
{
  "response": "Based on the retrieved context...",
  "relevant_documents": [...],
  "conversation_id": "conversation-id",
  "retrieved_count": 3
}
```

---

### 5. Get All Documents
**GET** `/rag/documents`

Get all documents for the authenticated user.

**Query Parameters:**
- `skip`: Number of documents to skip (default: 0)
- `limit`: Maximum number of documents to return (default: 20)
- `document_type`: Filter by document type ("text" or "video")

**Response:**
```json
{
  "documents": [...],
  "count": 10,
  "skip": 0,
  "limit": 20
}
```

---

### 6. Delete Document
**DELETE** `/rag/documents/{document_id}`

Delete a document by ID.

**Response:**
```json
{
  "message": "Document deleted successfully",
  "document_id": "uuid-here"
}
```

---

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file in the Backend directory:
```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
OPENAI_API_KEY=your_openai_api_key
```

### 3. Database Setup
Run the SQL commands in `DATABASE_SCHEMA.sql` in your Supabase SQL editor to create the necessary tables and functions.

### 4. Create Storage Bucket
In Supabase dashboard, create a storage bucket named "videos" for storing video files.

### 5. Run the Server
```bash
cd Backend/src
uvicorn main:app --reload
```

---

## Notes

- **Embeddings**: Uses OpenAI's `text-embedding-3-small` model (1536 dimensions)
- **Video Processing**: Uses OpenAI Whisper for transcription
- **Vector Search**: Uses pgvector extension in Supabase for efficient similarity search
- **Authentication**: All endpoints require valid JWT tokens from Supabase Auth

## Performance Considerations

- For large datasets, consider using the RPC function `match_documents` in Supabase for more efficient vector search
- Video processing can be slow for large files; consider implementing async job queues for production
- Embeddings are generated synchronously; consider batching for multiple documents

