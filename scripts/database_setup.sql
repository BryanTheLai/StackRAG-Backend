-- Enable the pgvector extension to store and search vector embeddings
-- Requires enabling it in the Supabase UI under Database -> Extensions first
create extension if not exists "vector";

-- Enable uuid-ossp extension for uuid_generate_v4()
create extension if not exists "uuid-ossp";

-- Drop tables if they exist (useful for development/resetting)
-- In production, be very careful with dropping tables!
drop table if exists chunks cascade; -- Use cascade to drop dependent objects
drop table if exists sections cascade;
drop table if exists documents cascade;

-- Create the documents table
create table documents (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid references auth.users(id) not null, -- Link to Supabase Auth user
    filename text not null,
    storage_path text not null, -- Path in Supabase Storage
    upload_timestamp timestamp with time zone default now(),
    status text default 'processing' not null, -- e.g., 'uploaded', 'processing', 'completed', 'failed'

    -- Extracted Metadata (Dedicated Columns for Filtering)
    doc_type text not null, -- e.g., 'pdf', 'docx'
    doc_specific_type text, -- e.g., 'Balance Sheet', 'Income Statement'
    company_name text,
    report_date date,
    doc_year integer,
    doc_quarter integer, -- 1-4 or null

    -- Full Markdown Content (NEW COLUMN)
    full_markdown_content text,

    -- Extracted Metadata (JSONB for less structured/frequently filtered data)
    doc_summary text,
    metadata jsonb, -- e.g., currency, units, sent_by, sent_to, other companies mentioned

    -- Ensure user_id is indexed for fast lookups
    constraint fk_user foreign key (user_id) references auth.users(id) on delete cascade
);

-- Add indexes for performance
create index documents_user_id_idx on documents (user_id);
create index documents_type_year_quarter_idx on documents (doc_specific_type, doc_year, doc_quarter);
create index documents_report_date_idx on documents (report_date);
create index documents_company_name_idx on documents (company_name);


-- Create the sections table
create table sections (
    id uuid primary key default uuid_generate_v4(),
    document_id uuid references documents(id) on delete cascade not null, -- Link to parent document
    user_id uuid references auth.users(id) not null, -- Redundant but useful for direct RLS

    section_heading text, -- e.g., 'Revenue Analysis'
    page_numbers integer[], -- Array of page numbers covered
    content_markdown text not null, -- The full markdown content of the section
    section_index integer not null, -- Order of the section in the document

    -- Ensure user_id and document_id are indexed
    constraint fk_document foreign key (document_id) references documents(id) on delete cascade,
    constraint fk_user_section foreign key (user_id) references auth.users(id) on delete cascade -- Ensure user consistency
);

-- Add indexes
create index sections_document_id_idx on sections (document_id);
create index sections_user_id_idx on sections (user_id);


-- Create the chunks table
create table chunks (
    id uuid primary key default uuid_generate_v4(),
    section_id uuid references sections(id) on delete cascade not null, -- Link to parent section
    document_id uuid references documents(id) on delete cascade not null, -- Redundant but useful for RLS and direct queries
    user_id uuid references auth.users(id) not null, -- Redundant but crucial for RLS

    chunk_text text not null, -- The text content of the chunk
    chunk_index integer not null, -- Order within its section/document
    start_char_index integer, -- Start character index in parent section markdown
    end_char_index integer, -- End character index in parent section markdown

    -- Embedding vector (adjust vector size based on your model, e.g., 1536 for OpenAI ada-002)
    embedding vector(1536),
    embedding_model text, -- Name or identifier of the model used

    -- Copied Metadata (for Filtering & Embedding Context) - Indexed where useful
    doc_specific_type text,
    doc_year integer,
    doc_quarter integer,
    company_name text,
    report_date date,
    section_heading text, -- Copy section heading here for easier filtering/embedding context

    -- Ensure keys and relevant metadata are indexed
    constraint fk_section foreign key (section_id) references sections(id) on delete cascade,
    constraint fk_document_chunk foreign key (document_id) references documents(id) on delete cascade,
    constraint fk_user_chunk foreign key (user_id) references auth.users(id) on delete cascade -- Ensure user consistency
);

-- Add indexes
create index chunks_section_id_idx on chunks (section_id);
create index chunks_document_id_idx on chunks (document_id);
create index chunks_user_id_idx on chunks (user_id);
-- Indexes on copied metadata for filtering BEFORE vector search
create index chunks_type_year_quarter_idx on chunks (doc_specific_type, doc_year, doc_quarter);
create index chunks_report_date_idx on chunks (report_date);
create index chunks_company_name_idx on chunks (company_name);
-- Index for vector search (hnsw recommended for performance)
-- Adjust lists based on your specific needs and performance testing
create index chunks_embedding_idx on chunks using hnsw (embedding vector_cosine_ops);


-- Set up Row Level Security (RLS)
-- RLS is OFF by default; enable it on each table
alter table documents enable row level security;
alter table sections enable row level security;
alter table chunks enable row level security;

-- Policies allow users to see/manage ONLY their own data
-- Using the more granular policies suggested by Supabase AI for better control

-- Policies for documents table
create policy "User can select their own documents" on documents
  for select
  to authenticated
  using (auth.uid() = user_id);

create policy "User can insert their own documents" on documents
  for insert
  to authenticated
  with check (auth.uid() = user_id);

create policy "User can update their own documents" on documents
  for update
  to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "User can delete their own documents" on documents
  for delete
  to authenticated
  using (auth.uid() = user_id);

-- Policies for sections table
create policy "User can select their own sections" on sections
  for select
  to authenticated
  using (auth.uid() = user_id);

create policy "User can insert their own sections" on sections
  for insert
  to authenticated
  with check (auth.uid() = user_id);

create policy "User can update their own sections" on sections
  for update
  to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "User can delete their own sections" on sections
  for delete
  to authenticated
  using (auth.uid() = user_id);

-- Policies for chunks table
create policy "User can select their own chunks" on chunks
  for select
  to authenticated
  using (auth.uid() = user_id);

create policy "User can insert their own chunks" on chunks
  for insert
  to authenticated
  with check (auth.uid() = user_id);

create policy "User can update their own chunks" on chunks
  for update
  to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "User can delete their own chunks" on chunks
  for delete
  to authenticated
  using (auth.uid() = user_id);