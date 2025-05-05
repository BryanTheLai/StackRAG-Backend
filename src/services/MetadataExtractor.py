# src/services/MetadataExtractor.py
from google.genai import types
from src.llm.GeminiClient import GeminiClient
from src.enums import FinancialDocSpecificType
from pydantic import BaseModel, Field
from src.prompts.prompt_manager import PromptManager

class FinancialDocumentMetadata(BaseModel):
    """Structured document metadata."""
    doc_specific_type: FinancialDocSpecificType = Field(
        ..., description="Specific type of financial report."
    )
    company_name: str = Field(
        ..., description="Primary company name."
    )
    report_date: str # YYYY-MM-DD format
    doc_year: int = Field(
        ..., description="Primary fiscal year."
    )
    doc_quarter: int = Field(
        ..., description="Primary fiscal quarter (1-4). -1 if not quarterly."
    )
    doc_summary: str = Field(
        ..., description="Brief summary."
    )

class MetadataExtractor:
    """
    Extracts metadata from markdown using an LLM and Pydantic schema.
    """

    def __init__(self, gemini_client: GeminiClient = None):
        """
        Initialize extractor with a Gemini client.
        """
        self.gemini_client = gemini_client or GeminiClient()
        self.text_model = "gemini-2.0-flash-lite" # Model supporting JSON schema

    def extract_metadata(self, markdown_text_snippet: str, truncate_length: int = 16000) -> FinancialDocumentMetadata:
        """
        Sends text snippet to LLM to extract structured metadata.
        """
        truncated = markdown_text_snippet[:truncate_length]

        formatted_prompt = PromptManager.get_prompt(
            "metadata_extraction",
            document_text_snippet=truncated
        )

        print("Sending text snippet to LLM for structured metadata extraction…")
        response = self.gemini_client.client.models.generate_content(
            model=self.text_model,
            contents=[formatted_prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FinancialDocumentMetadata
            )
        )

        extracted_metadata: FinancialDocumentMetadata = response.parsed

        if extracted_metadata:
            print("Structured metadata extraction attempted.")

        return extracted_metadata