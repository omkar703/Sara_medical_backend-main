"""Database Initialization Script for PostgreSQL"""

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
CREATE EXTENSION IF NOT EXISTS "vector";   -- pgvector for AI embeddings (future use)

-- Set timezone
SET timezone = 'UTC';

-- Create initial indexes for performance
-- (More will be added via Alembic migrations)

COMMENT ON EXTENSION "uuid-ossp" IS 'UUID generation functions';
COMMENT ON EXTENSION "pg_trgm" IS 'Text similarity measurement using trigrams';
COMMENT ON EXTENSION "vector" IS 'Vector data type and operations for AI embeddings';
