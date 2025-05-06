# src/models/ingestion_models.py

import uuid
from typing import Dict, Any

ParsingResult = Dict[str, Any] # Contains 'markdown_content', 'page_count', 'error'

SectionData = Dict[str, Any] # Contains 'document_id', 'user_id', 'section_heading',
                             # 'page_numbers', 'content_markdown', 'section_index', 'id' (after saving)

ChunkData = Dict[str, Any] # Contains 'section_id', 'document_id', 'user_id',
                           # 'chunk_text', 'chunk_index', 'start_char_index', 'end_char_index',
                           # 'embedding', 'embedding_model', 'doc_specific_type',
                           # 'doc_year', 'doc_quarter', 'company_name', 'report_date',
                           # 'section_heading', 'metadata'