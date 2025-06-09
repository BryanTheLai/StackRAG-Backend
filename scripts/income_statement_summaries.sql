-- Creates a dedicated table for storing the 3-metric summary of income statements.
-- This approach is modular and optimized for time-series dashboard queries.

-- Ensure the uuid-ossp extension is available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create the table
CREATE TABLE public.income_statement_summaries (
    -- Primary Key for the summary record itself
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- A UNIQUE foreign key to the source document.
    -- This ensures one summary per document. Deletes cascade.
    document_id UUID NOT NULL UNIQUE REFERENCES public.documents(id) ON DELETE CASCADE,

    -- User ID for multi-tenancy and Row Level Security
    user_id UUID NOT NULL,

    -- The 3 Core Metrics. NUMERIC is used for financial data to prevent float precision errors.
    -- NUMERIC(18, 4) supports up to 14 digits before the decimal point.
    total_revenue NUMERIC(18, 4) NOT NULL,
    total_expenses NUMERIC(18, 4) NOT NULL,
    net_income NUMERIC(18, 4) NOT NULL,

    -- Metadata for the summary
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    period_start_date DATE NOT NULL,
    period_end_date DATE NOT NULL,

    -- Standard timestamp columns
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Add comments for clarity
COMMENT ON TABLE public.income_statement_summaries IS 'Stores high-level, 3-metric summaries of income statements for fast dashboarding.';
COMMENT ON COLUMN public.income_statement_summaries.document_id IS 'One-to-one link to the source document in the documents table.';
COMMENT ON COLUMN public.income_statement_summaries.total_revenue IS 'Total revenue for the period.';
COMMENT ON COLUMN public.income_statement_summaries.total_expenses IS 'Calculated total expenses for the period (Revenue - Net Income).';
COMMENT ON COLUMN public.income_statement_summaries.net_income IS 'Final net income (profit or loss) for the period.';


-- ######### INDEXES FOR PERFORMANCE #########
-- This composite index is CRITICAL for fast "revenue over time" dashboard queries.
CREATE INDEX idx_summaries_timeseries ON public.income_statement_summaries (user_id, period_end_date DESC);


-- ######### ROW LEVEL SECURITY (RLS) #########
-- Enable RLS to ensure data privacy
ALTER TABLE public.income_statement_summaries ENABLE ROW LEVEL SECURITY;

-- Create policies to enforce that users can only interact with their own data.
CREATE POLICY "Users can select their own income statement summaries"
    ON public.income_statement_summaries FOR SELECT
    TO authenticated USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own income statement summaries"
    ON public.income_statement_summaries FOR INSERT
    TO authenticated WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own income statement summaries"
    ON public.income_statement_summaries FOR UPDATE
    TO authenticated USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own income statement summaries"
    ON public.income_statement_summaries FOR DELETE
    TO authenticated USING (auth.uid() = user_id);
