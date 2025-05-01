# src/services/MetadataExtractor.py
from google.genai import types
from src.llm.GeminiClient import GeminiClient
from src.enums import FinancialDocSpecificType
from pydantic import BaseModel, Field

class FinancialDocumentMetadata(BaseModel):
    """Pydantic model for structured financial document metadata."""
    doc_specific_type: FinancialDocSpecificType = Field(
        ..., description="The specific type of financial report."
    )
    company_name: str = Field(
        ..., description="The primary company name the report is about."
    )
    report_date: str # YYYY-MM-DD format as a string
    doc_year: int = Field(
        ..., description="The primary fiscal year the report covers."
    )
    doc_quarter: int = Field(
        ..., description="The primary fiscal quarter the report covers (1-4). Use -1 if not a quarterly report."
    )
    doc_summary: str = Field(
        ..., description="A brief summary of the document's purpose or highlights."
    )

class MetadataExtractor:
    """
    Extracts structured document-level metadata and a summary
    from the beginning of a document's markdown content using a text-based LLM,
    constrained by a Pydantic schema.
    """

    METADATA_EXTRACTION_PROMPT = """
    You are an expert financial document analyst.
    Analyze the provided text, which is the beginning of a financial report.
    Extract the structured metadata requested by the schema provided in the configuration.
    
    Extract the following fields based *only* on the content of the text snippet:
    - doc_specific_type: The type of financial report. Choose from the allowed list.
    - company_name: The primary company name.
    - report_date: The most relevant date (YYYY-MM-DD).
    - doc_year: The primary fiscal year (integer).
    - doc_quarter: The primary fiscal quarter (1-4 integer). If not a quarterly report or quarter is not found, use -1.
    - doc_summary: A brief, 1-2 sentence summary.
    
    If a specific piece of information (like company name, date, year, quarter) is genuinely not found in the text snippet, use an empty string "" for text fields, -1 for integer fields like year/quarter, and "1900-01-01" or a similar clear placeholder for the date if you cannot find it, according to the schema.
    
    Provide the response strictly as a JSON object conforming to the requested schema. Do not include any other text or commentary.
    
    ---TEXT_START---
    {document_text_snippet}
    ---TEXT_END---
    """
    # Note: Using the format method to insert the text snippet into the prompt string.

    def __init__(self, gemini_client: GeminiClient = None):
        """
        Initialize metadata extractor with a Gemini client.
        Uses default GeminiClient if none provided.
        """
        self.gemini_client = gemini_client or GeminiClient()
        # Use a text-based model suitable for structured extraction and schema
        # Ensure this model supports response_schema and application/json mime type
        self.text_model = "gemini-2.0-flash-lite"

    def extract_metadata(self, markdown_text_snippet: str, truncate_length: int = 16000) -> FinancialDocumentMetadata:
        """
        Sends a snippet of document markdown text to an LLM to extract structured metadata,
        constrained by the Pydantic schema.

        Args:
            markdown_text_snippet: The beginning part of the document's combined markdown.
            truncate_length: Maximum number of characters to send to the LLM (rough estimate).

        Returns:
            An instance of FinancialDocumentMetadata, or None if parsing fails.
        """
        truncated_text = markdown_text_snippet[:truncate_length]

        formatted_prompt = self.METADATA_EXTRACTION_PROMPT.format(
            document_text_snippet=truncated_text.replace('{', '{{').replace('}', '}}')
        )

        print("Sending text snippet to LLM for structured metadata extraction...")
        response = self.gemini_client.client.models.generate_content(
            model=self.text_model,
            contents=[formatted_prompt], # Send the prompt as text content
            config=types.GenerateContentConfig(
                response_mime_type="application/json", # Request JSON output
                response_schema=FinancialDocumentMetadata # Constrain using our Pydantic model
            )
        )

        extracted_metadata: FinancialDocumentMetadata = response.parsed

        if extracted_metadata:
            print("Structured metadata extraction attempted.")

        return extracted_metadata # Will be FinancialDocumentMetadata instance or None