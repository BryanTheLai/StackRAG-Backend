-- Create processing_jobs table to track document processing status
-- This allows users to refresh the page and still see processing status

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing table if you need to recreate
DROP TABLE IF EXISTS public.processing_jobs CASCADE;

CREATE TABLE public.processing_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    document_id UUID REFERENCES public.documents(id) ON DELETE SET NULL,
    filename TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, parsing, extracting_metadata, sectioning, chunking, embedding, completed, failed
    current_step TEXT, -- SHORT message for UI display (max 50 chars)
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    error_message TEXT, -- User-friendly error message
    error_code TEXT, -- Technical error code for debugging (api_key_invalid, file_corrupted, etc)
    retry_count INTEGER DEFAULT 0, -- How many times user retried
    result_data JSONB, -- Store success response
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- Index for fast user queries
CREATE INDEX idx_processing_jobs_user_id ON public.processing_jobs(user_id);
CREATE INDEX idx_processing_jobs_status ON public.processing_jobs(status);
CREATE INDEX idx_processing_jobs_created_at ON public.processing_jobs(created_at DESC);

-- RLS Policies: Users can only see their own jobs
ALTER TABLE public.processing_jobs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own processing jobs
CREATE POLICY "Users can view own processing jobs"
    ON public.processing_jobs
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can insert their own processing jobs
CREATE POLICY "Users can create own processing jobs"
    ON public.processing_jobs
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own processing jobs
CREATE POLICY "Users can update own processing jobs"
    ON public.processing_jobs
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_processing_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER processing_jobs_updated_at
    BEFORE UPDATE ON public.processing_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_processing_jobs_updated_at();

-- Optional: Auto-cleanup completed jobs after 7 days
-- Uncomment if you want automatic cleanup
-- CREATE OR REPLACE FUNCTION cleanup_old_processing_jobs()
-- RETURNS void AS $$
-- BEGIN
--     DELETE FROM public.processing_jobs
--     WHERE completed_at < (now() - INTERVAL '7 days')
--     AND status IN ('completed', 'failed');
-- END;
-- $$ LANGUAGE plpgsql;

SELECT 'Processing jobs table created successfully!' AS status;
