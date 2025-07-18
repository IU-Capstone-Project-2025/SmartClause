CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE EXTENSION IF NOT EXISTS vector;

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

CREATE TABLE IF NOT EXISTS rule_chunks (
    chunk_id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES rules(rule_id) ON DELETE CASCADE,
    chunk_number INTEGER,
    chunk_text TEXT,
    chunk_char_start INTEGER,
    chunk_char_end INTEGER,
    embedding vector(1024),
    chunk_tsv tsvector GENERATED ALWAYS AS (
        to_tsvector('russian', coalesce(chunk_text, ''))
    ) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(255),
    user_id VARCHAR(255),
    analysis_points JSONB,
    content_hash VARCHAR(64),
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '1 hour'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS rule_chunks_embedding_idx ON rule_chunks USING hnsw (embedding vector_l2_ops) WITH (m = 8, ef_construction = 64);
CREATE INDEX IF NOT EXISTS rule_chunks_chunk_tsv ON rule_chunks USING GIN (chunk_tsv);
CREATE INDEX IF NOT EXISTS rules_rule_number_idx ON rules (rule_number);
CREATE INDEX IF NOT EXISTS rules_file_idx ON rules (file);
CREATE INDEX IF NOT EXISTS rule_chunks_rule_id_idx ON rule_chunks (rule_id);
CREATE INDEX IF NOT EXISTS rule_chunks_chunk_number_idx ON rule_chunks (rule_id, chunk_number);

-- Indexes for analysis results
CREATE INDEX IF NOT EXISTS analysis_results_document_id_idx ON analysis_results (document_id);
CREATE INDEX IF NOT EXISTS analysis_results_user_id_idx ON analysis_results (user_id);
CREATE INDEX IF NOT EXISTS analysis_results_document_user_idx ON analysis_results (document_id, user_id);

-- Indexes for caching
CREATE INDEX IF NOT EXISTS analysis_results_content_hash_expires_idx ON analysis_results (content_hash, expires_at);
CREATE INDEX IF NOT EXISTS analysis_results_user_hash_expires_idx ON analysis_results (user_id, content_hash, expires_at);
CREATE INDEX IF NOT EXISTS analysis_results_expires_cleanup_idx ON analysis_results (expires_at); 