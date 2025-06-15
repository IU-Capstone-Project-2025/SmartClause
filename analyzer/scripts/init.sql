-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Table for storing legal rules (articles) from the Civil Code
CREATE TABLE IF NOT EXISTS legal_rules (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255),
    rule_number INTEGER,
    rule_title TEXT,
    rule_text TEXT,
    section_title TEXT,
    chapter_title TEXT,
    start_char INTEGER,
    end_char INTEGER,
    text_length INTEGER,
    embedding vector(1024), -- Embedding dimension for BGE-M3
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for storing document embeddings for RAG retrieval
CREATE TABLE IF NOT EXISTS document_embeddings (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(255) UNIQUE,
    text_chunk TEXT,
    embedding vector(1024),
    document_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for storing analysis results
CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(255),
    analysis_points JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient similarity search
CREATE INDEX IF NOT EXISTS legal_rules_embedding_idx ON legal_rules USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS document_embeddings_embedding_idx ON document_embeddings USING ivfflat (embedding vector_cosine_ops);

-- Index for rule number lookup
CREATE INDEX IF NOT EXISTS legal_rules_rule_number_idx ON legal_rules (rule_number);

-- Index for document ID lookup
CREATE INDEX IF NOT EXISTS document_embeddings_document_id_idx ON document_embeddings (document_id);
CREATE INDEX IF NOT EXISTS analysis_results_document_id_idx ON analysis_results (document_id); 