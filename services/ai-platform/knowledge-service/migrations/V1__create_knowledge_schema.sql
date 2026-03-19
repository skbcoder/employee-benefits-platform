-- Knowledge schema for RAG document storage and vector search
-- Requires pgvector extension

CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS knowledge;

-- Source documents with metadata
CREATE TABLE knowledge.document (
    document_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           TEXT NOT NULL,
    source          TEXT,
    category        TEXT NOT NULL,
    content         TEXT NOT NULL,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Document chunks with vector embeddings
CREATE TABLE knowledge.document_chunk (
    chunk_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES knowledge.document(document_id) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    token_count     INTEGER NOT NULL,
    embedding       vector(768),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX idx_chunk_document ON knowledge.document_chunk(document_id);
CREATE INDEX idx_document_category ON knowledge.document(category);

-- IVFFlat index for cosine similarity search (create after initial data load for best results)
-- For small datasets, exact search is fine. Uncomment when you have >1000 chunks:
-- CREATE INDEX idx_chunk_embedding ON knowledge.document_chunk
--     USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
