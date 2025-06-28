-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Table for storing legal rules (articles) from Russian legal codes
-- Corresponds to dataset_codes_rf.csv structure
CREATE TABLE IF NOT EXISTS rules (
    rule_id SERIAL PRIMARY KEY,
    file VARCHAR(255),
    rule_number INTEGER,
    rule_title TEXT,
    rule_text TEXT,
    section_title TEXT,
    chapter_title TEXT,
    start_char INTEGER,
    end_char INTEGER,
    text_length INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for storing rule chunks with embeddings
-- Corresponds to rule_chunks_table.csv structure from chunked dataset
CREATE TABLE IF NOT EXISTS rule_chunks (
    chunk_id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES rules(rule_id) ON DELETE CASCADE,
    chunk_number INTEGER,
    chunk_text TEXT,
    chunk_char_start INTEGER,
    chunk_char_end INTEGER,
    embedding vector(1024), -- Embedding dimension for BGE-M3
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for storing analysis results
CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(255),
    analysis_points JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient similarity search on embeddings using HNSW
-- Parameters based on benchmarking: m=8, ef_construction=64 for optimal accuracy/speed tradeoff (based on experiments/indexing.ipynb experement)
CREATE INDEX IF NOT EXISTS rule_chunks_embedding_idx ON rule_chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 8, ef_construction = 64);

-- Indexes for efficient lookups
CREATE INDEX IF NOT EXISTS rules_rule_number_idx ON rules (rule_number);
CREATE INDEX IF NOT EXISTS rules_file_idx ON rules (file);
CREATE INDEX IF NOT EXISTS rule_chunks_rule_id_idx ON rule_chunks (rule_id);
CREATE INDEX IF NOT EXISTS rule_chunks_chunk_number_idx ON rule_chunks (rule_id, chunk_number);

-- Index for analysis results
CREATE INDEX IF NOT EXISTS analysis_results_document_id_idx ON analysis_results (document_id); 