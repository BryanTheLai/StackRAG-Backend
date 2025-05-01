# src/pipeline.py

import time
import uuid
from typing import IO, Optional, Dict, Any
import io # Import io for type checks

# Import all necessary service classes and data structures
from src.llm.GeminiClient import GeminiClient
from src.llm.OpenAIClient import OpenAIClient
from src.services.FinancialDocParser import FinancialDocParser, ParsingResult
from src.services.MetadataExtractor import MetadataExtractor, FinancialDocumentMetadata
from src.services.Sectioner import Sectioner
from src.services.ChunkingService import ChunkingService
from src.services.EmbeddingService import EmbeddingService
from src.services.SupabaseService import SupabaseService

# Define a simple result structure for the pipeline run
PipelineResult = Dict[str, Any]

class IngestionPipeline:
    """
    Orchestrates the document ingestion process, calling various services
    to parse, analyze, chunk, embed, and store financial documents.
    """

    def __init__(
        self,
        financial_doc_parser: Optional[FinancialDocParser] = None,
        metadata_extractor: Optional[MetadataExtractor] = None,
        sectioner: Optional[Sectioner] = None,
        chunking_service: Optional[ChunkingService] = None,
        embedding_service: Optional[EmbeddingService] = None,
        supabase_service: Optional[SupabaseService] = None
    ):
        """
        Initialize the pipeline with instances of all required services.
        If a service is not provided, it attempts to create a default instance.
        """
        print("Initializing IngestionPipeline...")

        # Initialize clients first if needed by multiple services
        # In a real app, these might be singletons or managed differently
        gemini_client = GeminiClient()
        openai_client = OpenAIClient()
        # Pass authenticated Supabase client if available, otherwise service creates its own
        # For this example, we assume SupabaseService will handle client creation/auth context
        supabase_client = None # Or pass your authenticated client here if testing setup requires

        # Instantiate services, passing dependencies or allowing defaults
        self.parser = financial_doc_parser or FinancialDocParser(gemini_client=gemini_client)
        self.metadata_extractor = metadata_extractor or MetadataExtractor(gemini_client=gemini_client)
        self.sectioner = sectioner or Sectioner()
        self.chunking_service = chunking_service or ChunkingService() # Uses default chonkie settings
        self.embedding_service = embedding_service or EmbeddingService(openai_client=openai_client)
        self.supabase_service = supabase_service or SupabaseService(supabase_client=supabase_client)

        print("IngestionPipeline initialized with all services.")


    def run(
        self,
        pdf_file_buffer: IO[bytes],
        user_id: uuid.UUID,
        original_filename: str,
        doc_type: str # e.g., 'pdf' - determined before calling pipeline
    ) -> PipelineResult:
        """
        Executes the full ingestion pipeline for a single document.

        Args:
            pdf_file_buffer: File-like object (buffer) containing PDF bytes.
            user_id: The UUID of the authenticated user processing the file.
            original_filename: The original name of the uploaded file.
            doc_type: The file type ('pdf', etc.).

        Returns:
            A dictionary indicating success or failure, and relevant IDs/messages.
        """
        print(f"\n--- Starting Ingestion Pipeline for: {original_filename} (User: {user_id}) ---")
        start_time = time.time()

        document_id: Optional[uuid.UUID] = None # To store the ID once created

        try:
            # --- Step 1: Parse PDF to Markdown ---
            print("\nStep 1: Parsing PDF to Markdown...")
            parsing_result: ParsingResult = self.parser.parse_pdf_to_markdown(pdf_file_buffer)
            if parsing_result.get("error") or not parsing_result.get("markdown_content"):
                error_msg = f"Parsing failed: {parsing_result.get('error', 'No markdown content generated.')}"
                print(error_msg)
                return {"success": False, "message": error_msg}
            combined_markdown = parsing_result["markdown_content"]
            page_count = parsing_result["page_count"]
            print(f"Parsing successful ({page_count} pages). Markdown length: {len(combined_markdown)}")

            # --- Step 2: Extract Document Metadata ---
            print("\nStep 2: Extracting Document Metadata...")
            # Use only the beginning of the markdown for efficiency
            markdown_snippet = combined_markdown[:16000] # Use same limit as extractor default
            metadata_result: FinancialDocumentMetadata = self.metadata_extractor.extract_metadata(markdown_snippet)

            if not metadata_result: # MetadataExtractor returns None on failure
                 # Failure handled within extract_metadata now, returns None
                 error_msg = "Metadata extraction failed (Extractor returned None)."
                 print(error_msg)
                 # Cannot proceed without metadata to save document record meaningfully
                 return {"success": False, "message": error_msg}
            document_metadata: FinancialDocumentMetadata = metadata_result
            print("Metadata extraction successful.")
            print(f"  Extracted Type: {document_metadata.doc_specific_type.value if document_metadata.doc_specific_type else 'None'}")
            print(f"  Extracted Company: {document_metadata.company_name}")

            # --- Step 3: Upload Original PDF to Storage ---
            # Generate a UUID for the document path *before* saving the record
            # This ID is primarily for the storage path structure in this flow
            document_id_for_path = uuid.uuid4()
            print(f"\nStep 3: Uploading Original PDF (using temp ID for path: {document_id_for_path})...")
            storage_path = self.supabase_service.upload_pdf_to_storage(
                pdf_file_buffer=pdf_file_buffer, # Pass buffer again
                user_id=user_id,
                document_id=document_id_for_path,
                original_filename=original_filename
            )
            if not storage_path:
                 error_msg = "Failed to upload original PDF to storage."
                 print(error_msg)
                 return {"success": False, "message": error_msg}
            print(f"Original PDF uploaded successfully to: {storage_path}")


            # --- Step 4: Save Document Record to Database ---
            print("\nStep 4: Saving Document Record to Database...")
            document_id = self.supabase_service.save_document_record(
                user_id=user_id,
                filename=original_filename,
                storage_path=storage_path,
                doc_type=doc_type,
                metadata=document_metadata, # Pass the Pydantic model
                full_markdown_content=combined_markdown

            )
            if not document_id:
                 error_msg = "Failed to save document record to database."
                 print(error_msg)
                 # Consider attempting to delete the uploaded storage file here for cleanup
                 return {"success": False, "message": error_msg}
            print(f"Document record saved successfully. Document ID: {document_id}")


            # --- Step 5: Section Markdown ---
            print("\nStep 5: Sectioning Markdown Content...")
            sections_data = self.sectioner.section_markdown(
                markdown_content=combined_markdown,
                document_id=document_id, # Use the actual document ID now
                user_id=user_id
            )
            if not sections_data:
                 # Might be okay if document was empty, but log a warning
                 print("Warning: No sections were generated from the markdown.")
                 # Proceed, but likely no chunks will be generated either

            # --- Step 6: Save Sections Batch ---
            print("\nStep 6: Saving Sections to Database...")
            # Add necessary IDs before saving if not already present
            for section in sections_data:
                 section['document_id'] = document_id
                 section['user_id'] = user_id
                 # The section ID ('id') will be generated by the DB upon insert

            saved_section_ids = self.supabase_service.save_sections_batch(sections_data)

            if saved_section_ids is None: # Service returns None on failure
                 error_msg = "Failed to save sections batch to database."
                 print(error_msg)
                 self.supabase_service.update_document_status(document_id, "failed")
                 return {"success": False, "message": error_msg, "document_id": document_id}
            elif len(saved_section_ids) != len(sections_data):
                 print(f"Warning: Number of saved section IDs ({len(saved_section_ids)}) does not match number of sections ({len(sections_data)}).")
                 # Continue, but there might be an issue

            # Add the generated DB IDs back to the sections_data for chunking service
            if len(saved_section_ids) == len(sections_data):
                for i, section in enumerate(sections_data):
                     section['id'] = saved_section_ids[i]
            else:
                 print("Skipping adding section IDs due to count mismatch.")
                 # Chunking might fail if section IDs are missing

            print(f"Sections saved successfully ({len(saved_section_ids)} sections).")

            # --- Step 7: Chunk Sections ---
            print("\nStep 7: Chunking Sections...")
            chunks_data = self.chunking_service.chunk_sections(
                sections=sections_data, # Pass sections with DB IDs if available
                document_metadata=document_metadata,
                document_id=document_id,
                user_id=user_id
            )
            if not chunks_data:
                 print("Warning: No chunks were generated.")
                 # If no chunks, the process is technically complete but with no searchable content
                 self.supabase_service.update_document_status(document_id, "completed_no_chunks")
                 total_time = time.time() - start_time
                 print(f"\n--- Ingestion Pipeline Completed (No Chunks) for {original_filename} in {total_time:.2f} seconds ---")
                 return {"success": True, "message": "Pipeline completed, but no chunks were generated.", "document_id": document_id, "chunk_count": 0}


            # --- Step 8: Generate Embeddings ---
            print("\nStep 8: Generating Embeddings...")
            chunks_with_embeddings = self.embedding_service.generate_embeddings(chunks_data)
            # Check if embeddings were added (simple check: look for 'embedding' key in first chunk)
            if not chunks_with_embeddings or 'embedding' not in chunks_with_embeddings[0]:
                 # Handle potential embedding failure (service might return original list)
                 error_msg = "Failed to generate embeddings or add them to chunk data."
                 print(error_msg)
                 self.supabase_service.update_document_status(document_id, "failed")
                 return {"success": False, "message": error_msg, "document_id": document_id}
            print("Embeddings generated successfully.")


            # --- Step 9: Save Chunks Batch ---
            print("\nStep 9: Saving Chunks with Embeddings to Database...")
            save_chunks_success = self.supabase_service.save_chunks_batch(chunks_with_embeddings)

            if not save_chunks_success:
                 error_msg = "Failed to save chunks batch to database."
                 print(error_msg)
                 self.supabase_service.update_document_status(document_id, "failed")
                 return {"success": False, "message": error_msg, "document_id": document_id}
            print("Chunks saved successfully.")


            # --- Step 10: Finalize - Update Document Status ---
            print("\nStep 10: Updating Document Status to Completed...")
            status_update_success = self.supabase_service.update_document_status(document_id, "completed")
            if not status_update_success:
                # Log warning but consider pipeline successful overall if chunks were saved
                print("Warning: Failed to update final document status to 'completed'.")


            # --- Pipeline Complete ---
            total_time = time.time() - start_time
            print(f"\n--- Ingestion Pipeline Successfully Completed for {original_filename} in {total_time:.2f} seconds ---")
            return {
                "success": True,
                "message": "Document processed and ingested successfully.",
                "document_id": document_id,
                "chunk_count": len(chunks_with_embeddings)
            }

        except Exception as e:
            # Catch any unexpected error during the pipeline execution
            error_msg = f"An unexpected error occurred in the ingestion pipeline: {e}"
            print(error_msg)
            # Attempt to update status to failed if we have a document ID
            if document_id:
                 print(f"Attempting to mark document {document_id} as failed...")
                 self.supabase_service.update_document_status(document_id, "failed")
            # Return failure result
            return {"success": False, "message": error_msg, "document_id": document_id}