-- Supabase SQL Editor - Command 2

-- Create or replace a function for searching chunks by vector similarity, filtered by user_id
CREATE OR REPLACE FUNCTION match_chunks (
  query_embedding vector(1536), -- The embedding vector of the search query
  match_count int,               -- How many closest chunks to return
  user_id uuid                   -- The ID of the user whose documents we are searching
)
-- Updated RETURNS TABLE to only include columns present in the chunks table
RETURNS TABLE (
  id uuid,
  chunk_text text,
  document_id uuid,
  section_id uuid,
  section_heading text, -- section_heading is copied to the chunks table
  chunk_index integer,
  doc_specific_type text, -- metadata copied to chunks table
  doc_year integer,       -- metadata copied to chunks table
  doc_quarter integer,    -- metadata copied to chunks table
  company_name text,      -- metadata copied to chunks table
  report_date date,       -- metadata copied to chunks table
  similarity_score float         -- The calculated similarity score (computed in the SELECT)
)
LANGUAGE plpgsql
AS $$
BEGIN
  -- Return chunks where the user_id matches the provided user_id,
  -- ordered by cosine distance to the query_embedding (lower is closer),
  -- and calculate the similarity score.
  RETURN QUERY
  SELECT
    chunks.id,
    chunks.chunk_text,
    chunks.document_id,
    chunks.section_id,
    chunks.section_heading, -- Select section_heading as it exists in chunks
    chunks.chunk_index,
    chunks.doc_specific_type,
    chunks.doc_year,
    chunks.doc_quarter,
    chunks.company_name,
    chunks.report_date,
    (chunks.embedding <=> query_embedding) as similarity_score -- Cosine distance operator
  FROM chunks
  WHERE chunks.user_id = match_chunks.user_id -- Filter by the user_id passed to the function
  ORDER BY chunks.embedding <=> query_embedding
  LIMIT match_count; -- Limit the number of results as requested
END;
$$;