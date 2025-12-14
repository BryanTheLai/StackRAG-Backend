# src/pipeline.py

import time
import uuid
from typing import IO, Optional, Dict, Any

from src.llm.GeminiClient import GeminiClient
from src.llm.OpenAIClient import OpenAIClient
from src.services.FinancialDocParser import FinancialDocParser
from src.services.MetadataExtractor import MetadataExtractor

from src.models.ingestion_models import ParsingResult, SectionData, ChunkData

from src.models.metadata_models import FinancialDocumentMetadata
from src.enums import FinancialDocSpecificType # ADDED IMPORT

from src.services.Sectioner import Sectioner
from src.services.ChunkingService import ChunkingService
from src.services.EmbeddingService import EmbeddingService
from src.storage.SupabaseService import SupabaseService

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
        Initialize the pipeline with instances of required services.
        Creates defaults if not provided.
        """
        print("Initializing IngestionPipeline...")

        gemini_client = GeminiClient()
        openai_client = OpenAIClient()
        supabase_client = None

        self.parser = financial_doc_parser or FinancialDocParser(gemini_client=gemini_client)
        self.metadata_extractor = metadata_extractor or MetadataExtractor(gemini_client=gemini_client)
        self.sectioner = sectioner or Sectioner()
        self.chunking_service = chunking_service or ChunkingService()
        self.embedding_service = embedding_service or EmbeddingService(openai_client=openai_client)
        self.supabase_service = supabase_service or SupabaseService(supabase_client=supabase_client)

        print("IngestionPipeline initialized with all services.")


    def _update_job_progress(self, job_id: Optional[uuid.UUID], status: str, step: str, progress: int):
        """Helper to update processing job progress in database."""
        if not job_id:
            return
        try:
            self.supabase_service.client.table("processing_jobs").update({
                "status": status,
                "current_step": step,
                "progress_percentage": progress
            }).eq("id", str(job_id)).execute()
        except Exception as e:
            print(f"Warning: Failed to update job progress: {e}")

    async def run(
        self,
        pdf_file_buffer: IO[bytes],
        user_id: uuid.UUID,
        original_filename: str,
        doc_type: str,
        job_id: Optional[uuid.UUID] = None
    ) -> PipelineResult:
        """
        Executes the full ingestion pipeline for a single document.

        Args:
            pdf_file_buffer: File buffer containing PDF bytes.
            user_id: UUID of the authenticated user.
            original_filename: The original filename.
            doc_type: The file type ('pdf', etc.).
            job_id: Optional processing job ID for progress updates.

        Returns:
            A dictionary indicating success or failure.
        """
        print(f"\n--- Starting Ingestion Pipeline for: {original_filename} (User: {user_id}) ---")
        start_time = time.time()

        document_id: Optional[uuid.UUID] = None

        try:
            # --- Step 1: Parse PDF to Markdown ---
            print("\nStep 1: Parsing PDF to Markdown...")
            self._update_job_progress(job_id, "parsing", "Reading PDF...", 15)
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
            self._update_job_progress(job_id, "extracting_metadata", "Analyzing content...", 25)
            markdown_snippet = combined_markdown

            metadata_result, metadata_rate_limited = self.metadata_extractor.extract_metadata(
                markdown_snippet,
                original_filename=original_filename,
                forced_doc_specific_type=None,
            )

            if not metadata_result:
                 error_msg = "Metadata extraction failed."
                 print(error_msg)
                 return {"success": False, "message": error_msg}
            document_metadata: FinancialDocumentMetadata = metadata_result
            print("Metadata extraction successful.")
            print(f"  Extracted Type: {document_metadata.doc_specific_type.value if document_metadata.doc_specific_type else 'None'}")
            print(f"  Extracted Company: {document_metadata.company_name}")
            print(
                "  Extracted Income Fields: "
                f"revenue={getattr(document_metadata, 'total_revenue', None)} "
                f"expenses={getattr(document_metadata, 'total_expenses', None)} "
                f"net_income={getattr(document_metadata, 'net_income', None)} "
                f"period_end_date={getattr(document_metadata, 'period_end_date', None)} "
                f"currency={getattr(document_metadata, 'currency', None)}"
            )

            required_for_summary = {
                "total_revenue": getattr(document_metadata, "total_revenue", None),
                "total_expenses": getattr(document_metadata, "total_expenses", None),
                "net_income": getattr(document_metadata, "net_income", None),
                "period_end_date": getattr(document_metadata, "period_end_date", None),
            }
            missing_for_summary = [k for k, v in required_for_summary.items() if v is None]
            if missing_for_summary and not metadata_rate_limited:
                print(
                    "Income statement required fields missing after metadata extraction: "
                    f"{', '.join(missing_for_summary)}. Attempting focused LLM extraction for income fields..."
                )
                fields = self.metadata_extractor.extract_income_statement_fields(
                    markdown_snippet,
                    original_filename=original_filename,
                )
                if fields:
                    for attr in [
                        "total_revenue",
                        "total_expenses",
                        "net_income",
                        "currency",
                        "period_start_date",
                        "period_end_date",
                    ]:
                        current_val = getattr(document_metadata, attr, None)
                        new_val = getattr(fields, attr, None)
                        if current_val is None and new_val is not None:
                            setattr(document_metadata, attr, new_val)

                    print(
                        "  After second pass income fields: "
                        f"revenue={getattr(document_metadata, 'total_revenue', None)} "
                        f"expenses={getattr(document_metadata, 'total_expenses', None)} "
                        f"net_income={getattr(document_metadata, 'net_income', None)} "
                        f"period_end_date={getattr(document_metadata, 'period_end_date', None)} "
                        f"currency={getattr(document_metadata, 'currency', None)}"
                    )
            elif missing_for_summary and metadata_rate_limited:
                print(
                    "Income statement required fields missing, but metadata extraction was quota-limited; "
                    "skipping second-pass income field extraction to avoid extra quota burn."
                )

            # --- Step 3: Upload Original PDF to Storage ---
            document_id_for_path = uuid.uuid4()
            print(f"\nStep 3: Uploading Original PDF (using temp ID for path: {document_id_for_path})...")
            self._update_job_progress(job_id, "uploading", "Saving file...", 35)
            storage_path = self.supabase_service.upload_pdf_to_storage(
                pdf_file_buffer=pdf_file_buffer,
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
                metadata=document_metadata,
                full_markdown_content=combined_markdown

            )
            if not document_id:
                 error_msg = "Failed to save document record to database."
                 print(error_msg)
                 return {"success": False, "message": error_msg}
            print(f"Document record saved successfully. Document ID: {document_id}")

            # --- Step 4.5: Save Income Statement Summary (when required fields are present) ---
            required_for_summary = {
                "total_revenue": getattr(document_metadata, "total_revenue", None),
                "total_expenses": getattr(document_metadata, "total_expenses", None),
                "net_income": getattr(document_metadata, "net_income", None),
                "period_end_date": getattr(document_metadata, "period_end_date", None),
            }
            missing_for_summary = [k for k, v in required_for_summary.items() if v is None]

            if missing_for_summary:
                print(
                    f"\nSkipping Income Statement Summary for document: {document_id} "
                    f"(missing: {', '.join(missing_for_summary)}; doc_specific_type={document_metadata.doc_specific_type.value if document_metadata.doc_specific_type else 'None'})."
                )
            else:
                print(
                    f"\nAttempting to save Income Statement Summary for document: {document_id} "
                    f"(doc_specific_type={document_metadata.doc_specific_type.value if document_metadata.doc_specific_type else 'None'})."
                )
                summary_id = self.supabase_service.save_income_statement_summary(
                    document_id=document_id,
                    user_id=user_id,
                    metadata=document_metadata,
                )
                if summary_id:
                    print(f"Income Statement Summary saved successfully. Summary ID: {summary_id}")
                else:
                    print(f"Warning: Failed to save Income Statement Summary for document: {document_id}. Pipeline will continue.")
            # --- End Step ---

            # --- Step 5: Section Markdown ---
            print("\nStep 5: Sectioning Markdown Content...")
            self._update_job_progress(job_id, "sectioning", "Organizing content...", 50)
            sections_data = self.sectioner.section_markdown(
                markdown_content=combined_markdown,
                document_id=document_id,
                user_id=user_id
            )
            if not sections_data:
                 print("Warning: No sections were generated from the markdown.")


            # --- Step 6: Save Sections Batch ---
            print("\nStep 6: Saving Sections to Database...")
            for section in sections_data:
                 section['document_id'] = document_id
                 section['user_id'] = user_id

            saved_section_ids = self.supabase_service.save_sections_batch(sections_data)

            if saved_section_ids is None:
                 error_msg = "Failed to save sections batch to database."
                 print(error_msg)
                 self.supabase_service.update_document_status(document_id, "failed")
                 return {"success": False, "message": error_msg, "document_id": document_id}
            elif len(saved_section_ids) != len(sections_data):
                 print(f"Warning: Number of saved section IDs ({len(saved_section_ids)}) does not match number of sections ({len(sections_data)}).")

            if len(saved_section_ids) == len(sections_data):
                for i, section in enumerate(sections_data):
                     section['id'] = saved_section_ids[i]
            else:
                 print("Skipping adding section IDs due to count mismatch.")

            print(f"Sections saved successfully ({len(saved_section_ids)} sections).")

            # --- Step 7: Chunk Sections ---
            print("\nStep 7: Chunking Sections...")
            self._update_job_progress(job_id, "chunking", "Preparing data...", 65)
            chunks_data = self.chunking_service.chunk_sections(
                sections=sections_data,
                document_metadata=document_metadata,
                document_id=document_id,
                user_id=user_id
            )
            if not chunks_data:
                 print("Warning: No chunks were generated.")
                 self.supabase_service.update_document_status(document_id, "completed_no_chunks")
                 total_time = time.time() - start_time
                 print(f"\n--- Ingestion Pipeline Completed (No Chunks) for {original_filename} in {total_time:.2f} seconds ---")
                 return {"success": True, "message": "Pipeline completed, but no chunks were generated.", "document_id": document_id, "chunk_count": 0}


            # --- Step 8: Generate Embeddings ---
            print("\nStep 8: Generating Embeddings...")
            self._update_job_progress(job_id, "embedding", "Processing with AI...", 80)
            chunks_with_embeddings = self.embedding_service.generate_embeddings(chunks_data)
            if not chunks_with_embeddings or 'embedding' not in chunks_with_embeddings[0]:
                 error_msg = "Failed to generate embeddings or add them to chunk data."
                 print(error_msg)
                 self.supabase_service.update_document_status(document_id, "failed")
                 return {"success": False, "message": error_msg, "document_id": document_id}
            print("Embeddings generated successfully.")


            # --- Step 9: Save Chunks Batch ---
            print("\nStep 9: Saving Chunks with Embeddings to Database...")
            self._update_job_progress(job_id, "saving", "Finalizing...", 90)
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
            error_msg = f"An unexpected error occurred in the ingestion pipeline: {e}"
            print(error_msg)
            if document_id:
                 print(f"Attempting to mark document {document_id} as failed...")
                 self.supabase_service.update_document_status(document_id, "failed")
            return {"success": False, "message": error_msg, "document_id": document_id}