-- SQL for Profiles Table Setup
-- Author: AI CFO Assistant Engineering
-- Date: July 02, 2025 18:42
-- Version: 1.1 (Corrected)

-- This script creates a 'profiles' table linked one-to-one with 'auth.users'
-- and includes a trigger to automatically create a profile on new user signup.

-- 1. Create the 'profiles' table
-- The table schema is designed to store user-specific information that is not part of Supabase Auth.
CREATE TABLE public.profiles (
    -- The 'id' column serves as both the Primary Key and the Foreign Key,
    -- referencing auth.users. This enforces a strict one-to-one relationship.
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,

    full_name TEXT,
    company_name TEXT,
    role_in_company TEXT,

    -- JSONB is used for flexible, unstructured settings. It's indexed for performance.
    -- Defaulting to an empty JSON object '{}' prevents null reference errors in application code.
    app_settings JSONB DEFAULT '{}'::jsonb,

    -- Timestamps for tracking record changes. 'created_at' is set once, 'updated_at' on every modification.
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Add comments for clarity and maintainability, following best practices.
COMMENT ON TABLE public.profiles IS 'Stores user profile information, extending the auth.users table.';
COMMENT ON COLUMN public.profiles.id IS 'A one-to-one link to the user''s auth.users id.';
COMMENT ON COLUMN public.profiles.full_name IS 'The user''s full name.';
COMMENT ON COLUMN public.profiles.company_name IS 'The name of the company the user belongs to.';
COMMENT ON COLUMN public.profiles.role_in_company IS 'The user''s role or title within their company.';
COMMENT ON COLUMN public.profiles.app_settings IS 'Flexible JSONB field for storing user-specific application preferences (e.g., theme, notification settings).';
COMMENT ON COLUMN public.profiles.created_at IS 'Timestamp of when the profile was initially created.';
COMMENT ON COLUMN public.profiles.updated_at IS 'Timestamp of the last time the profile was updated.';


-- 2. Add Indexes
-- A GIN index on the JSONB column is highly recommended for performant querying of app settings.
CREATE INDEX IF NOT EXISTS idx_profiles_app_settings_gin ON public.profiles USING GIN (app_settings);


-- 3. Row-Level Security (RLS)
-- Enable RLS to ensure users can only access their own profile data.
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Create policies for SELECT, INSERT, UPDATE, and DELETE.
-- These policies are the security backbone for a multi-tenant application.
CREATE POLICY "Users can view their own profile"
    ON public.profiles FOR SELECT
    TO authenticated
    USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
    ON public.profiles FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON public.profiles FOR UPDATE
    TO authenticated
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can delete their own profile"
    ON public.profiles FOR DELETE
    TO authenticated
    USING (auth.uid() = id);


-- 4. Automatic Profile Creation Trigger
-- This function and trigger automate the creation of a profile entry whenever a new user signs up.
CREATE OR REPLACE FUNCTION public.fn_create_user_profile()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER -- This allows the function to run with the privileges of the user that defined it, bypassing RLS for this specific action.
SET search_path = public -- CORRECTED: This is now a function property, without a semicolon.
AS $$
BEGIN
  -- Insert a new row into public.profiles, setting the id to the new user's id.
  -- Extract metadata from user signup if available
  INSERT INTO public.profiles (
    id,
    full_name,
    company_name,
    role_in_company
  )
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'full_name', NULL),
    COALESCE(NEW.raw_user_meta_data->>'company_name', NULL),
    COALESCE(NEW.raw_user_meta_data->>'role_in_company', NULL)
  );
  RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.fn_create_user_profile() IS 'Automatically creates a profile for a new user upon signup.';

-- Drop the trigger if it already exists to ensure a clean setup.
DROP TRIGGER IF EXISTS trg_create_user_profile_on_signup ON auth.users;

-- Create the trigger that fires AFTER a new user is inserted into auth.users.
CREATE TRIGGER trg_create_user_profile_on_signup
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.fn_create_user_profile();


-- 5. 'updated_at' Timestamp Trigger
-- Reuse the existing function from 'chat_sessions.sql' to keep the codebase DRY.
-- This block is idempotent and safe to run even if the function already exists.
CREATE OR REPLACE FUNCTION public.fn_update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   IF row(NEW.*) IS DISTINCT FROM row(OLD.*) THEN
      NEW.updated_at = now();
      RETURN NEW;
   ELSE
      RETURN OLD;
   END IF;
END;
$$ LANGUAGE 'plpgsql';

COMMENT ON FUNCTION public.fn_update_updated_at_column() IS 'Generic trigger function to update the updated_at column to the current timestamp on row modification.';

-- Apply the trigger to the profiles table.
CREATE TRIGGER trg_profiles_update_updated_at
BEFORE UPDATE ON public.profiles
FOR EACH ROW
EXECUTE FUNCTION public.fn_update_updated_at_column();


-- Final confirmation message
SELECT 'Profiles table, RLS policies, and automatic creation trigger setup complete.';