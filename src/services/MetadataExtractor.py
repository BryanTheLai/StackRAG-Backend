# src/services/MetadataExtractor.py
from google.genai import types
from src.llm.GeminiClient import GeminiClient
from src.prompts.prompt_manager import PromptManager
from src.models.metadata_models import FinancialDocumentMetadata
from src.config.gemini_config import TEXT_MODEL


class MetadataExtractor:
    """
    Extracts metadata from markdown using an LLM and Pydantic schema.
    """

    def __init__(self, gemini_client: GeminiClient = None):
        """
        Initialize extractor with a Gemini client.
        """
        self.gemini_client = gemini_client or GeminiClient()
        self.text_model = TEXT_MODEL  # Use text model from config

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