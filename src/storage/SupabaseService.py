# src/services/SupabaseService.py

import os
import uuid
from typing import List, Optional, IO
from dotenv import load_dotenv
from supabase import create_client, Client
from src.models.ingestion_models import SectionData, ChunkData
from src.models.metadata_models import FinancialDocumentMetadata


class SupabaseService:
    """Handles storage and database operations with Supabase."""
    STORAGE_BUCKET_NAME = "financial-pdfs"

    def __init__(self, supabase_client: Optional[Client] = None):
        """Initializes the SupabaseService."""
        if supabase_client:
            self.client = supabase_client
            print("SupabaseService initialized with provided client.")
        else:
            print("SupabaseService initializing new client from environment variables...")
            load_dotenv()
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_ANON_KEY")

            if not supabase_url or not supabase_key:
                raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables.")

            self.client: Client = create_client(supabase_url, supabase_key)
            print("SupabaseService initialized new client successfully.")

    def upload_pdf_to_storage(
        self,
        pdf_file_buffer: IO[bytes],
        user_id: uuid.UUID,
        document_id: uuid.UUID,
        original_filename: str
    ) -> Optional[str]:
        """Uploads a PDF buffer to user's storage path."""
        storage_path = f"{str(user_id)}/{str(document_id)}/{original_filename}"
        print(f"Attempting to upload PDF to storage path: {storage_path}")

        try:
            pdf_file_buffer.seek(0)
            pdf_bytes = pdf_file_buffer.read()

            self.client.storage.from_(self.STORAGE_BUCKET_NAME).upload(
                path=storage_path,
                file=pdf_bytes,
                file_options={"cache-control": "3600", "upsert": "false"}
            )
            print(f"Supabase storage upload response for {storage_path}")

            print(f"PDF successfully uploaded to: {storage_path}")
            return storage_path

        except Exception as e:
            print(f"Error uploading PDF to Supabase Storage at {storage_path}: {e}")
            if "duplicate key value violates unique constraint" in str(e) or \
               "The resource already exists" in str(e):
                 print(f"Hint: File likely already exists at this path and upsert is false.")
            elif "security policy" in str(e):
                 print(f"Hint: RLS policy likely denied the upload. Check path prefix and policies.")
            return None

    def save_document_record(
        self,
        user_id: uuid.UUID,
        filename: str,
        storage_path: str,
        doc_type: str,
        metadata: FinancialDocumentMetadata,
        full_markdown_content: str
    ) -> Optional[uuid.UUID]:
        """Saves the main document record to the 'documents' table."""
        print(f"Saving document record for: {filename} (User: {user_id})")
        try:
            document_data = {
                "user_id": str(user_id),
                "filename": filename,
                "storage_path": storage_path,
                "doc_type": doc_type,
                "doc_specific_type": metadata.doc_specific_type.value if metadata.doc_specific_type else None,
                "company_name": metadata.company_name if metadata.company_name else None,
                "report_date": metadata.report_date, # Simplified: Pydantic model ensures it's str or None
                "doc_year": metadata.doc_year if metadata.doc_year != -1 else None,
                "doc_quarter": metadata.doc_quarter if metadata.doc_quarter != -1 else None,
                "doc_summary": metadata.doc_summary,
                "full_markdown_content": full_markdown_content,
                "metadata": {"currency": None, "units": None}, # Placeholder JSONB
                "status": "processing"
            }

            response = self.client.table('documents').insert(document_data).execute()

            if response.data and len(response.data) > 0:
                 inserted_record = response.data[0]
                 document_id = uuid.UUID(inserted_record['id'])
                 print(f"Document record saved successfully. Document ID: {document_id}")
                 return document_id
            else:
                 print(f"Failed to save document record. Response data: {response.data}")
                 if hasattr(response, 'error') and response.error:
                    print(f"Supabase error: {response.error}")
                 return None

        except Exception as e:
            print(f"Error saving document record to Supabase DB: {e}")
            return None

    def save_sections_batch(self, sections: List[SectionData]) -> Optional[List[uuid.UUID]]:
        """Saves a batch of section records to the 'sections' table."""
        if not sections:
            return []

        print(f"Saving batch of {len(sections)} section records...")
        try:
            section_payload = [
                {
                    "document_id": str(s['document_id']),
                    "user_id": str(s['user_id']),
                    "section_heading": s.get('section_heading'),
                    "page_numbers": s.get('page_numbers', []),
                    "content_markdown": s.get('content_markdown', ''),
                    "section_index": s.get('section_index', 0)
                } for s in sections
            ]

            response = self.client.table('sections').insert(section_payload).execute()

            if response.data and len(response.data) == len(sections):
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
        """Saves a batch of chunk records to the 'chunks' table."""
        if not chunks:
            return True

        print(f"Saving batch of {len(chunks)} chunk records...")
        try:
            chunk_payload = []
            for c in chunks:
                if 'embedding' not in c or not isinstance(c.get('embedding'), list):
                     print(f"Warning: Chunk missing valid embedding, skipping chunk: {c.get('chunk_index')} in section {c.get('section_id')}")
                     continue

                chunk_payload.append({
                    "section_id": str(c['section_id']),
                    "document_id": str(c['document_id']),
                    "user_id": str(c['user_id']),
                    "chunk_text": c.get('chunk_text', ''),
                    "chunk_index": c.get('chunk_index'),
                    "start_char_index": c.get('start_char_index'),
                    "end_char_index": c.get('end_char_index'),
                    "embedding": c.get('embedding'),
                    "embedding_model": c.get('embedding_model'),
                    "doc_specific_type": c.get('doc_specific_type'),
                    "doc_year": c.get('doc_year'),
                    "doc_quarter": c.get('doc_quarter'),
                    "company_name": c.get('company_name'),
                    "report_date": c.get('report_date'),
                    "section_heading": c.get('section_heading'),
                })

            if not chunk_payload:
                 print("No valid chunks with embeddings found to save.")
                 return False

            print(f"Attempting bulk insert of {len(chunk_payload)} chunks...")
            response = self.client.table('chunks').insert(chunk_payload).execute()

            if response.data and len(response.data) == len(chunk_payload):
                 print(f"Batch of {len(chunk_payload)} chunks likely saved successfully.")
                 return True
            else:
                 print(f"Failed to save chunks batch or unexpected response count. Expected {len(chunk_payload)}, response data: {response.data}")
                 if hasattr(response, 'error') and response.error:
                    print(f"Supabase error: {response.error}")
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

    def save_income_statement_summary(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        metadata: FinancialDocumentMetadata
    ) -> Optional[uuid.UUID]:
        """Saves an income statement summary to the 'income_statement_summaries' table."""
        print(f"Attempting to save income statement summary for document_id: {document_id} by user_id: {user_id}")

        required_fields = {
            "total_revenue": metadata.total_revenue,
            "total_expenses": metadata.total_expenses,
            "net_income": metadata.net_income,
            "period_end_date": metadata.period_end_date
        }

        missing_fields = [field_name for field_name, value in required_fields.items() if value is None]

        if missing_fields:
            print(f"Error: Missing required financial data fields: {', '.join(missing_fields)} in metadata for document {document_id}. Cannot save summary.")
            return None

        summary_data_payload = {
            "document_id": str(document_id),
            "user_id": str(user_id),
            "total_revenue": metadata.total_revenue,
            "total_expenses": metadata.total_expenses,
            "net_income": metadata.net_income,
            "period_start_date": metadata.period_start_date, # Expected 'YYYY-MM-DD'
            "period_end_date": metadata.period_end_date,     # Expected 'YYYY-MM-DD'
        }

        # Handle currency: SQL table has NOT NULL DEFAULT 'USD'.
        # If metadata.currency is provided, use it. Otherwise, omit from payload to use DB default.
        if metadata.currency is not None:
            summary_data_payload["currency"] = metadata.currency
        else:
            print(f"Info: Currency not provided in metadata for document {document_id}. Relying on database default 'USD'.")


        try:
            print(f"Executing insert for income statement summary with payload: {summary_data_payload}")
            response = self.client.table('income_statement_summaries').insert(summary_data_payload).execute()

            if response.data and len(response.data) > 0:
                inserted_summary = response.data[0]
                # The 'income_statement_summaries' table has its own 'id' as PK
                summary_id = uuid.UUID(inserted_summary['id'])
                print(f"Income statement summary saved successfully. Summary ID: {summary_id} for Document ID: {document_id}")
                return summary_id
            else:
                error_message = "Unknown error"
                if hasattr(response, 'error') and response.error:
                    error_message = response.error.message if hasattr(response.error, 'message') else str(response.error)
                print(f"Failed to save income statement summary for document {document_id}. Supabase response: {response.data}, Error: {error_message}")
                return None

        except Exception as e:
            error_str = str(e)
            print(f"Exception saving income statement summary for document {document_id}: {error_str}")
            # Check for unique constraint violation on document_id, as it's UNIQUE in income_statement_summaries
            if "duplicate key value violates unique constraint" in error_str and "income_statement_summaries_document_id_key" in error_str:
                print(f"Hint: An income statement summary for document_id {document_id} already exists.")
            elif "invalid input for type numeric" in error_str:
                 print(f"Hint: Check if numeric fields (revenue, expenses, net_income) are valid numbers.")
            elif "invalid input syntax for type date" in error_str:
                 print(f"Hint: Check if date fields (period_start_date, period_end_date) are in 'YYYY-MM-DD' format.")
            return None