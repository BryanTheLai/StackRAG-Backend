from typing import List
import uuid
from chonkie import RecursiveChunker
from src.models.ingestion_models import ChunkData, SectionData
from src.models.metadata_models import FinancialDocumentMetadata

class ChunkingService:
    """Split markdown into fixed-size chunks."""

    def __init__(self, chunk_size: int = 4096, min_characters_per_chunk: int = 1024):
        print("Initializing ChunkingService...")
        self.chunker = RecursiveChunker.from_recipe(
            "markdown", lang="en",
            chunk_size=chunk_size,
            min_characters_per_chunk=min_characters_per_chunk,
            return_type="chunks"
        )
        print(f"chunk_size={chunk_size}, min_chars={min_characters_per_chunk}")

    def chunk_sections(
        self,
        sections: List[SectionData],
        document_metadata: FinancialDocumentMetadata,
        document_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> List[ChunkData]:
        """Return flat list of chunk dicts."""
        print(f"Chunking {len(sections)} sections...")
        meta = {
            "doc_specific_type": getattr(document_metadata.doc_specific_type, "value", None),
            "doc_year": None if document_metadata.doc_year == -1 else document_metadata.doc_year,
            "doc_quarter": None if document_metadata.doc_quarter == -1 else document_metadata.doc_quarter,
            "company_name": document_metadata.company_name or None,
            "report_date": None if document_metadata.report_date == "1900-01-01" else document_metadata.report_date
        }
        all_chunks: List[ChunkData] = []
        for sec in sections:
            title = sec.get("section_heading", "Unknown")
            text = sec.get("content_markdown", "").strip()
            if not text:
                print(f"Skipping empty '{title}'"); continue

            print(f"Chunking '{title}'...")
            chunks = self.chunker.chunk(text)
            if not chunks:
                print(f"No chunks for '{title}'"); continue

            sec_id = sec.get("id", uuid.uuid4())
            for idx, c in enumerate(chunks):
                all_chunks.append({
                    **meta,
                    "section_id": sec_id,
                    "document_id": document_id,
                    "user_id": user_id,
                    "chunk_text": c.text,
                    "chunk_index": idx,
                    "start_char_index": c.start_index,
                    "end_char_index": c.end_index,
                    "section_heading": title,
                    "metadata": {}
                })
            print(f"'{title}' → {len(chunks)} chunks")

        print(f"Done: {len(all_chunks)} chunks total")
        return all_chunks