-- Create a schema if you want to group your app-specific tables (optional but good practice)
-- CREATE SCHEMA IF NOT EXISTS cfo_assistant_schema;
-- SET search_path TO cfo_assistant_schema, public; -- Use this if you create a schema

-- Ensure the uuid-ossp extension is available (should be from previous setup)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Define the chat_sessions table
CREATE TABLE public.chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT, -- Optional title for the conversation
    history JSONB NOT NULL, -- Stores the entire chat history array
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB -- For any extra unstructured info about the conversation
);

-- Add comments to table and columns for clarity
COMMENT ON TABLE public.chat_sessions IS 'Stores individual chat conversations, with the full history as JSONB.';
COMMENT ON COLUMN public.chat_sessions.id IS 'Unique identifier for the chat session.';
COMMENT ON COLUMN public.chat_sessions.user_id IS 'Owner of the chat session, references auth.users.';
COMMENT ON COLUMN public.chat_sessions.title IS 'User-friendly title for the conversation (e.g., auto-generated from first message).';
COMMENT ON COLUMN public.chat_sessions.history IS 'The complete conversation history as a JSONB array of turns.';
COMMENT ON COLUMN public.chat_sessions.created_at IS 'Timestamp of when the conversation was created.';
COMMENT ON COLUMN public.chat_sessions.updated_at IS 'Timestamp of the last update to the conversation.';
COMMENT ON COLUMN public.chat_sessions.metadata IS 'Optional JSONB field for additional conversation metadata (e.g., summary, tags).';


-- 2. Add Indexes
-- Index on user_id for efficient lookup of a user's conversations
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON public.chat_sessions(user_id);

-- Optional: GIN index for querying within the JSONB history.
-- This can be added later if complex JSON queries are frequent and need optimization.
-- For "shipping fast", it's okay to omit initially.
-- CREATE INDEX IF NOT EXISTS idx_chat_sessions_history_gin ON public.chat_sessions USING GIN (history);
/*
   Example query this GIN index would optimize:
   SELECT *
   FROM public.chat_sessions
   WHERE history @> '[{"role": "model", "parts": [{"function_call": {"name": "retrieve_financial_chunks"}}]}]';
*/

-- 3. Row-Level Security (RLS)
-- Enable RLS on the table
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;

-- Allow users to select their own chat sessions
CREATE POLICY "Users can select their own chat sessions"
    ON public.chat_sessions
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

-- Allow users to insert new chat sessions for themselves
CREATE POLICY "Users can insert their own chat sessions"
    ON public.chat_sessions
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

-- Allow users to update their own chat sessions (e.g., change title, append to history)
CREATE POLICY "Users can update their own chat sessions"
    ON public.chat_sessions
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id) -- Ensures they are updating their own record
    WITH CHECK (auth.uid() = user_id); -- Double-check on the new data

-- Allow users to delete their own chat sessions
CREATE POLICY "Users can delete their own chat sessions"
    ON public.chat_sessions
    FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);


-- 4. Trigger to automatically update 'updated_at' timestamp
-- Create the trigger function (if it doesn't already exist from other table setups in a compatible way)
CREATE OR REPLACE FUNCTION public.fn_update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   IF row(NEW.*) IS DISTINCT FROM row(OLD.*) THEN -- Only update if something actually changed
      NEW.updated_at = now();
      RETURN NEW;
   ELSE
      RETURN OLD; -- Return OLD to prevent an infinite loop if nothing changed
   END IF;
END;
$$ LANGUAGE 'plpgsql';

COMMENT ON FUNCTION public.fn_update_updated_at_column() IS 'Generic trigger function to update the updated_at column to the current timestamp on row modification.';

-- Apply the trigger to the chat_sessions table
CREATE TRIGGER trg_chat_sessions_update_updated_at
BEFORE UPDATE ON public.chat_sessions
FOR EACH ROW
EXECUTE FUNCTION public.fn_update_updated_at_column();

-- Grant USAGE on the schema to Supabase roles if you used a custom schema
-- GRANT USAGE ON SCHEMA cfo_assistant_schema TO postgres, anon, authenticated, service_role;
-- GRANT ALL ON ALL TABLES IN SCHEMA cfo_assistant_schema TO postgres, anon, authenticated, service_role;
-- GRANT ALL ON ALL FUNCTIONS IN SCHEMA cfo_assistant_schema TO postgres, anon, authenticated, service_role;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA cfo_assistant_schema TO postgres, anon, authenticated, service_role;

-- If not using a custom schema, and tables are in 'public', Supabase roles usually have necessary grants.

SELECT 'Chat sessions table setup complete.';