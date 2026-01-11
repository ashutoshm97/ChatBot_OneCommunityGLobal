-- Database Schema for RAG Chatbot
-- Run these SQL commands in your Supabase SQL editor

-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents table for storing text and video transcriptions with embeddings
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text TEXT NOT NULL,
    embedding vector(1536), -- OpenAI text-embedding-3-small produces 1536-dimensional vectors
    metadata JSONB DEFAULT '{}',
    document_type TEXT DEFAULT 'text', -- 'text' or 'video'
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on user_id for faster queries
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);

-- Create index on document_type
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);

-- Create index on embedding for vector similarity search (using HNSW for better performance)
CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents 
USING hnsw (embedding vector_cosine_ops);

-- Conversations table for storing chat history
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id TEXT, -- For grouping messages in a conversation
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    retrieved_docs JSONB DEFAULT '[]', -- Array of document IDs used in response
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on conversation_id and user_id
CREATE INDEX IF NOT EXISTS idx_conversations_conversation_id ON conversations(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);

-- RPC function for efficient vector similarity search
-- This function performs vector similarity search using pgvector
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5,
    user_filter uuid DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    text text,
    metadata jsonb,
    document_type text,
    similarity float,
    created_at timestamptz
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
        1 - (documents.embedding <=> query_embedding) as similarity,
        documents.created_at
    FROM documents
    WHERE 
        documents.embedding IS NOT NULL
        AND (user_filter IS NULL OR documents.user_id = user_filter)
        AND (1 - (documents.embedding <=> query_embedding)) > match_threshold
    ORDER BY documents.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Row Level Security (RLS) policies
-- Enable RLS on documents table
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own documents
CREATE POLICY "Users can view their own documents"
    ON documents FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can insert their own documents
CREATE POLICY "Users can insert their own documents"
    ON documents FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own documents
CREATE POLICY "Users can update their own documents"
    ON documents FOR UPDATE
    USING (auth.uid() = user_id);

-- Policy: Users can delete their own documents
CREATE POLICY "Users can delete their own documents"
    ON documents FOR DELETE
    USING (auth.uid() = user_id);

-- Enable RLS on conversations table
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own conversations
CREATE POLICY "Users can view their own conversations"
    ON conversations FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can insert their own conversations
CREATE POLICY "Users can insert their own conversations"
    ON conversations FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Create storage bucket for videos (run this in Supabase dashboard or via API)
-- You can also create this via Supabase dashboard: Storage > Create Bucket
-- Bucket name: 'videos'
-- Public: false (private bucket)

