-- scripts/storage_setup.sql

-- Create the Storage bucket
-- Ensure the bucket name follows the rules: lowercase letters, numbers, dots, hyphens
-- Set public to false for a private bucket where RLS controls access
insert into storage.buckets (id, name, public)
values ('financial-pdfs', 'financial-pdfs', false)
on conflict (id) do nothing; -- Avoid error if bucket already exists


-- Set up Row Level Security (RLS) for objects in this bucket
-- RLS on storage.objects is typically enabled by default in Supabase.
-- The following line might cause a syntax error if RLS is already enabled.
-- If you encountered an error here previously, it's safe to comment it out
-- as the RLS is likely already active.
-- alter table storage.objects enable row security;


-- Drop existing policies for this bucket if they exist (useful for development/resetting)
drop policy if exists "User can view their own files in financial-pdfs" on storage.objects;
drop policy if exists "User can upload files to their own folder in financial-pdfs" on storage.objects;
drop policy if exists "User can delete their own files in financial-pdfs" on storage.objects;
drop policy if exists "User can update their own files in financial-pdfs" on storage.objects;


-- Policy 1: Allow authenticated users to view (SELECT) files ONLY if the file path starts with their user_id/
-- Uses the syntax that worked for you: (select auth.uid())::text
create policy "User can view their own files in financial-pdfs"
  on storage.objects for select
  to authenticated
  using (
    bucket_id = 'financial-pdfs' AND -- Apply only to this bucket
    -- Check if the first folder segment in the object name (path) matches the authenticated user's UID
    -- We assume the path structure is '{user_id}/filename' or '{user_id}/folder/filename'
    (storage.foldername(name))[1] = (select auth.uid())::text -- User's preferred syntax
  );

-- Policy 2: Allow authenticated users to upload (INSERT) files ONLY into a folder named after their user_id
-- Uses the syntax that worked for you: (select auth.uid())::text
create policy "User can upload files to their own folder in financial-pdfs"
  on storage.objects for insert
  to authenticated
  with check ( -- 'with check' applies the policy to the new row being inserted
    bucket_id = 'financial-pdfs' AND -- Apply only to this bucket
    -- Check if the first folder segment in the object name (path) matches the authenticated user's UID
    (storage.foldername(name))[1] = (select auth.uid())::text -- User's preferred syntax
  );

-- Policy 3: Allow authenticated users to delete (DELETE) files ONLY from their own folder
-- Uses the syntax that worked for you: (select auth.uid())::text
create policy "User can delete their own files in financial-pdfs"
  on storage.objects for delete
  to authenticated
  using ( -- 'using' applies the policy to the existing row being deleted
    bucket_id = 'financial-pdfs' AND -- Apply only to this bucket
    -- Check if the first folder segment in the object name (path) matches the authenticated user's UID
    (storage.foldername(name))[1] = (select auth.uid())::text -- User's preferred syntax
  );

-- Policy 4: Allow authenticated users to update (UPDATE/UPSERT) files ONLY in their own folder
-- This is needed if you use upsert=True during upload to overwrite existing files
-- Uses the syntax that worked for you: (select auth.uid())::text
create policy "User can update their own files in financial-pdfs"
  on storage.objects for update
  to authenticated
  using ( -- 'using' applies to the old row before update
    bucket_id = 'financial-pdfs' AND
    (storage.foldername(name))[1] = (select auth.uid())::text -- User's preferred syntax
  )
  with check ( -- 'with check' applies to the new row after update
    bucket_id = 'financial-pdfs' AND
    (storage.foldername(name))[1] = (select auth.uid())::text -- User's preferred syntax
  );


-- Important Note on Path Structure:
-- These policies assume that the file path you use when uploading will start with the user's UID.
-- For example, if user UID is 'e222921f-cfdc-4a05-8cf2-aea13004bcf2',
-- you must upload to a path like 'e222921f-cfdc-4a05-8cf2-aea13004bcf2/invoice.pdf'
-- or 'e222921f-cfdc-4a05-8cf2-aea13004bcf2/reports/invoice.pdf'.
-- The policy checks (storage.foldername(name))[1] which extracts the *first* segment.