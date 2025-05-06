-- Supabase SQL Editor - Command 2 - Updated

-- Create or replace a function for searching chunks by vector similarity, filtered by user_id and optional metadata
CREATE OR REPLACE FUNCTION match_chunks (
  query_embedding vector(1536), -- The embedding vector of the search query
  match_count int,               -- How many closest chunks to return
  user_id uuid,                   -- The ID of the user whose documents we are searching

  -- New Optional Metadata Filters (with default NULL)
  p_doc_specific_type text DEFAULT NULL,
  p_company_name text DEFAULT NULL,
  p_doc_year_start integer DEFAULT NULL,
  p_doc_year_end integer DEFAULT NULL,
  p_doc_quarter integer DEFAULT NULL
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
  -- Return chunks filtered by the user_id and any provided metadata filters,
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
  WHERE
    chunks.user_id = match_chunks.user_id -- Filter by the user_id (required)

    -- Apply doc_specific_type filter if provided (not NULL)
    AND (p_doc_specific_type IS NULL OR chunks.doc_specific_type = p_doc_specific_type)

    -- Apply company_name filter if provided (not NULL and not empty)
    -- Using ILIKE for case-insensitivity and '%' for wildcard (contains)
    AND (p_company_name IS NULL OR p_company_name = '' OR chunks.company_name ILIKE '%' || p_company_name || '%')

    -- Apply doc_year range filter if start/end years are provided
    AND (p_doc_year_start IS NULL OR chunks.doc_year >= p_doc_year_start)
    AND (p_doc_year_end IS NULL OR chunks.doc_year <= p_doc_year_end)

    -- Apply doc_quarter filter if provided (not NULL)
    AND (p_doc_quarter IS NULL OR chunks.doc_quarter = p_doc_quarter)

  ORDER BY chunks.embedding <=> query_embedding
  LIMIT match_count; -- Limit the number of results as requested
END;
$$;