from __future__ import annotations

from typing import List, Tuple
import uuid

from src.models.ingestion_models import ChunkData, SectionData
from src.models.metadata_models import FinancialDocumentMetadata

class ChunkingService:
    """Split markdown into fixed-size chunks."""

    def __init__(self, chunk_size: int = 4096, min_characters_per_chunk: int = 1024):
        self.chunk_size = int(chunk_size)
        self.min_characters_per_chunk = int(min_characters_per_chunk)

        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if self.min_characters_per_chunk < 0:
            raise ValueError("min_characters_per_chunk must be >= 0")

    def _split_text(self, text: str) -> List[Tuple[int, int, str]]:
        if not text:
            return []

        n = len(text)
        chunks: List[Tuple[int, int, str]] = []
        start = 0

        while start < n:
            hard_end = min(start + self.chunk_size, n)
            if hard_end == n:
                raw = text[start:hard_end]
                if raw.strip():
                    chunks.append((start, hard_end, raw.strip()))
                break

            preferred_end = hard_end
            search_start = min(start + self.min_characters_per_chunk, n)
            if search_start < hard_end:
                window = text[search_start:hard_end]
                last_break_rel = max(window.rfind("\n\n"), window.rfind("\n"))
                if last_break_rel != -1:
                    preferred_end = search_start + last_break_rel

            if preferred_end <= start:
                preferred_end = hard_end

            raw = text[start:preferred_end]
            if raw.strip():
                chunks.append((start, preferred_end, raw.strip()))

            start = preferred_end

        return chunks

    def chunk_sections(
        self,
        sections: List[SectionData],
        document_metadata: FinancialDocumentMetadata,
        document_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> List[ChunkData]:
        """Return flat list of chunk dicts."""
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
                continue

            splits = self._split_text(text)
            if not splits:
                continue

            sec_id = sec.get("id", uuid.uuid4())
            for idx, (start_idx, end_idx, chunk_text) in enumerate(splits):
                all_chunks.append({
                    **meta,
                    "section_id": sec_id,
                    "document_id": document_id,
                    "user_id": user_id,
                    "chunk_text": chunk_text,
                    "chunk_index": idx,
                    "start_char_index": start_idx,
                    "end_char_index": end_idx,
                    "section_heading": title,
                    "metadata": {}
                })

        return all_chunks