# src/services/SupabaseService.py

import os
import io
import uuid
from datetime import date
from typing import List, Dict, Any, Optional, IO
from dotenv import load_dotenv
from supabase import create_client, Client # Import Supabase client library
# Import our data structures/types
from src.services.Sectioner import SectionData
from src.services.ChunkingService import ChunkData
from src.services.MetadataExtractor import FinancialDocumentMetadata

class SupabaseService:
    """
    Handles interactions with Supabase for storage and database operations
    related to the document ingestion pipeline. Assumes client is authenticated
    externally (e.g., via API middleware or notebook sign-in).
    """
    STORAGE_BUCKET_NAME = "financial-pdfs"

    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Initialize the SupabaseService.

        Args:
            supabase_client: An optional pre-initialized Supabase client.
                             If None, creates a new client using env vars.
        """
        if supabase_client:
            self.client = supabase_client
            print("SupabaseService initialized with provided client.")
        else:
            print("SupabaseService initializing new client from environment variables...")
            load_dotenv()
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_ANON_KEY") # Use ANON key usually

            if not supabase_url or not supabase_key:
                raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables.")

            # Note: For production, you might pass a service role key if this runs server-side
            # and bypasses RLS, but for client-side or user-context operations, ANON key is used.
            # The actual enforcement happens via RLS policies based on the authenticated user's JWT
            # which the supabase-py client manages after sign-in.
            self.client: Client = create_client(supabase_url, supabase_key)
            print("SupabaseService initialized new client successfully.")

    # --- Storage Operations ---

    # Inside the upload_pdf_to_storage method

    def upload_pdf_to_storage(
        self,
        pdf_file_buffer: IO[bytes],
        user_id: uuid.UUID,
        document_id: uuid.UUID, # Used for unique file path
        original_filename: str
    ) -> Optional[str]:
        """
        Uploads the PDF file buffer to the user's designated folder in Supabase Storage.

        Args:
            pdf_file_buffer: The file-like object (buffer) containing PDF bytes.
            user_id: The UUID of the authenticated user.
            document_id: The UUID assigned to the document record (for path).
            original_filename: The original name of the uploaded file.

        Returns:
            The storage path string if successful, None otherwise.
        """
        storage_path = f"{str(user_id)}/{str(document_id)}/{original_filename}"
        print(f"Attempting to upload PDF to storage path: {storage_path}")

        try:
            # Reset buffer position to the beginning before reading
            pdf_file_buffer.seek(0)
            # Read the entire content of the buffer into bytes
            pdf_bytes = pdf_file_buffer.read() # <<< CHANGE: Read bytes from buffer

            # Upload the raw bytes content
            response = self.client.storage.from_(self.STORAGE_BUCKET_NAME).upload(
                path=storage_path,
                file=pdf_bytes, # <<< CHANGE: Pass the bytes object
                file_options={"cache-control": "3600", "upsert": "false"}
            )
            print(f"Supabase storage upload response for {storage_path}")

            print(f"PDF successfully uploaded to: {storage_path}")
            return storage_path

        except Exception as e:
            # Catch potential StorageExceptions or other errors
            print(f"Error uploading PDF to Supabase Storage at {storage_path}: {e}")
            # Check for common errors based on string matching (fragile, but simple)
            if "duplicate key value violates unique constraint" in str(e) or \
               "The resource already exists" in str(e):
                 print(f"Hint: File likely already exists at this path and upsert is false.")
            elif "security policy" in str(e):
                 print(f"Hint: RLS policy likely denied the upload. Check path prefix and policies.")
            return None # Indicate failure

    # --- Database Operations ---

    def save_document_record(
        self,
        user_id: uuid.UUID,
        filename: str,
        storage_path: str,
        doc_type: str, # e.g., 'pdf'
        metadata: FinancialDocumentMetadata, 
        full_markdown_content: str
    ) -> Optional[uuid.UUID]:
        """
        Saves the main document record to the 'documents' table.

        Args:
            user_id: The owner's user ID.
            filename: The original filename.
            storage_path: The path where the file is stored in Supabase Storage.
            doc_type: The determined file type ('pdf', etc.).
            metadata: The FinancialDocumentMetadata object.
            full_markdown_content: The combined markdown from the parser.
        Returns:
            The generated UUID (document_id) of the new record if successful, None otherwise.
        """
        print(f"Saving document record for: {filename} (User: {user_id})")
        try:
            # Prepare the data payload matching the 'documents' table schema
            document_data = {
                "user_id": str(user_id),
                "filename": filename,
                "storage_path": storage_path,
                "doc_type": doc_type,
                # Extract values from the Pydantic model
                "doc_specific_type": metadata.doc_specific_type.value if metadata.doc_specific_type else None,
                "company_name": metadata.company_name if metadata.company_name else None,
                "report_date": metadata.report_date if metadata.report_date != "1900-01-01" else None, # Convert placeholder date
                "doc_year": metadata.doc_year if metadata.doc_year != -1 else None, # Convert placeholder year
                "doc_quarter": metadata.doc_quarter if metadata.doc_quarter != -1 else None, # Convert placeholder quarter
                "doc_summary": metadata.doc_summary,
                "full_markdown_content": full_markdown_content,

                # Add other JSONB metadata if needed (e.g., currency, units if extracted)
                "metadata": {"currency": None, "units": None}, # Placeholder JSONB
                "status": "processing" # Initial status after metadata extraction
            }

            # Perform the insert operation
            response = self.client.table('documents').insert(document_data).execute()

            # Check if the insert was successful (data should contain the inserted row)
            if response.data and len(response.data) > 0:
                 inserted_record = response.data[0]
                 document_id = uuid.UUID(inserted_record['id']) # Get the UUID generated by the DB
                 print(f"Document record saved successfully. Document ID: {document_id}")
                 return document_id
            else:
                 # This case might indicate an RLS issue preventing insertion or return
                 # or some other database constraint failure.
                 print(f"Failed to save document record. Response data: {response.data}")
                 if hasattr(response, 'error') and response.error:
                    print(f"Supabase error: {response.error}")
                 return None

        except Exception as e:
            print(f"Error saving document record to Supabase DB: {e}")
            return None

    def save_sections_batch(self, sections: List[SectionData]) -> Optional[List[uuid.UUID]]:
        """
        Saves a batch of section records to the 'sections' table.
        Assumes each section dict already contains 'document_id' and 'user_id'.

        Args:
            sections: A list of SectionData dictionaries.

        Returns:
            A list of the generated UUIDs (section_ids) if successful, None otherwise.
        """
        if not sections:
            return [] # Return empty list if no sections to save

        print(f"Saving batch of {len(sections)} section records...")
        try:
            # Prepare the list of dictionaries for bulk insert
            # Ensure required fields are present and types match DB (convert UUIDs to str)
            section_payload = [
                {
                    "document_id": str(s['document_id']),
                    "user_id": str(s['user_id']),
                    "section_heading": s.get('section_heading'),
                    "page_numbers": s.get('page_numbers', []), # Ensure it's a list
                    "content_markdown": s.get('content_markdown', ''),
                    "section_index": s.get('section_index', 0) # Ensure it has a value
                } for s in sections
            ]

            # Perform the bulk insert
            response = self.client.table('sections').insert(section_payload).execute()

            # Check if the insert was successful
            if response.data and len(response.data) == len(sections):
                 # Extract the generated UUIDs for each inserted section
                 section_ids = [uuid.UUID(record['id']) for record in response.data]
                 print(f"Batch of {len(section_ids)} sections saved successfully.")
                 return section_ids
            else:
                 print(f"Failed to save sections batch. Expected {len(sections)} records, response data: {response.data}")
                 if hasattr(response, 'error') and response.error:
                    print(f"Supabase error: {response.error}")
                 return None

        except Exception as e:
            print(f"Error saving sections batch to Supabase DB: {e}")
            return None


    def save_chunks_batch(self, chunks: List[ChunkData]) -> bool:
        """
        Saves a batch of chunk records (including embeddings) to the 'chunks' table.
        Assumes each chunk dict contains all necessary fields, including the embedding vector.

        Args:
            chunks: A list of ChunkData dictionaries with embedding vectors.

        Returns:
            True if the batch insert was likely successful, False otherwise.
        """
        if not chunks:
            return True # No chunks to save is considered success

        print(f"Saving batch of {len(chunks)} chunk records...")
        try:
            # Prepare the list of dictionaries for bulk insert
            # Convert UUIDs to str, ensure embedding is a list of floats
            chunk_payload = []
            for c in chunks:
                # Basic check for embedding presence and type
                if 'embedding' not in c or not isinstance(c.get('embedding'), list):
                     print(f"Warning: Chunk missing valid embedding, skipping chunk: {c.get('chunk_index')} in section {c.get('section_id')}")
                     continue # Skip chunks without embeddings for safety

                chunk_payload.append({
                    "section_id": str(c['section_id']),
                    "document_id": str(c['document_id']),
                    "user_id": str(c['user_id']),
                    "chunk_text": c.get('chunk_text', ''),
                    "chunk_index": c.get('chunk_index'),
                    "start_char_index": c.get('start_char_index'),
                    "end_char_index": c.get('end_char_index'),
                    "embedding": c.get('embedding'), # Pass the list of floats directly
                    "embedding_model": c.get('embedding_model'),
                    # Copied metadata
                    "doc_specific_type": c.get('doc_specific_type'),
                    "doc_year": c.get('doc_year'),
                    "doc_quarter": c.get('doc_quarter'),
                    "company_name": c.get('company_name'),
                    "report_date": c.get('report_date'), # Assumes string date matches DB 'date' type casting
                    "section_heading": c.get('section_heading'),
                    # metadata JSONB column is not populated in this simple version
                })

            if not chunk_payload:
                 print("No valid chunks with embeddings found to save.")
                 return False

            # Perform the bulk insert
            print(f"Attempting bulk insert of {len(chunk_payload)} chunks...")
            response = self.client.table('chunks').insert(chunk_payload).execute()

            # Check if the insert likely succeeded
            # With bulk inserts, success check is less precise without `returning='representation'`
            # Often, lack of an error and response.data having expected length indicates success.
            # RLS errors might still occur silently depending on Supabase version/config.
            if response.data and len(response.data) == len(chunk_payload):
                 print(f"Batch of {len(chunk_payload)} chunks likely saved successfully.")
                 return True
            else:
                 print(f"Failed to save chunks batch or unexpected response count. Expected {len(chunk_payload)}, response data: {response.data}")
                 if hasattr(response, 'error') and response.error:
                    print(f"Supabase error: {response.error}")
                 # Consider the operation failed if counts don't match
                 return False

        except Exception as e:
            print(f"Error saving chunks batch to Supabase DB: {e}")
            return False

    def update_document_status(self, document_id: uuid.UUID, status: str) -> bool:
        """Updates the status of a document record."""
        print(f"Updating status for document {document_id} to '{status}'")
        try:
            response = self.client.table('documents')\
                .update({"status": status})\
                .eq("id", str(document_id))\
                .execute()

            # Check if update likely succeeded (affected rows count might be in response meta)
            # For simplicity, we check if data is returned (often the updated row)
            if response.data and len(response.data) > 0:
                 print("Document status updated successfully.")
                 return True
            else:
                 print(f"Failed to update document status or no matching document found. Response: {response.data}")
                 if hasattr(response, 'error') and response.error:
                     print(f"Supabase error: {response.error}")
                 return False
        except Exception as e:
            print(f"Error updating document status: {e}")
            return False