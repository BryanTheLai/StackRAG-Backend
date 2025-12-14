# src/services/MetadataExtractor.py
from google.genai import types
from src.llm.GeminiClient import GeminiClient
from src.prompts.prompt_manager import PromptManager
from src.models.metadata_models import FinancialDocumentMetadata
from src.config.gemini_config import TEXT_MODEL
from src.enums import FinancialDocSpecificType
import re


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

    def extract_metadata(
        self,
        markdown_text_snippet: str,
        truncate_length: int = 16000,
        original_filename: str | None = None,
        forced_doc_specific_type: FinancialDocSpecificType | None = None,
    ) -> FinancialDocumentMetadata:
        """
        Sends text snippet to LLM to extract structured metadata.
        """
        truncated = (markdown_text_snippet or "")[:truncate_length]

        filename_hint = (original_filename or "").strip()
        forced_hint = forced_doc_specific_type.value if forced_doc_specific_type else ""
        preamble_lines: list[str] = []
        if filename_hint:
            preamble_lines.append(f"FILENAME: {filename_hint}")
        if forced_hint:
            preamble_lines.append(f"DOC_TYPE_HINT: {forced_hint}")

        if preamble_lines:
            truncated = "\n".join(preamble_lines) + "\n\n" + truncated

        formatted_prompt = PromptManager.get_prompt(
            "metadata_extraction",
            document_text_snippet=truncated
        )

        print("Sending text snippet to LLM for structured metadata extraction…")
        try:
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
        except Exception as e:
            error_text = str(e)
            is_quota = "resource_exhausted" in error_text.lower() or "quota exceeded" in error_text.lower() or "429" in error_text
            if not is_quota:
                raise

        return self._heuristic_metadata(truncated, original_filename=original_filename)

    def _heuristic_metadata(self, text: str, original_filename: str | None = None) -> FinancialDocumentMetadata:
        lower = (text or "").lower()
        file_lower = (original_filename or "").lower()

        if (
            "income statement" in lower
            or "statement of operations" in lower
            or "profit and loss" in lower
            or "p&l" in lower
            or "income statement" in file_lower
            or "income statements" in file_lower
            or "profit" in file_lower
        ):
            doc_type = FinancialDocSpecificType.INCOME_STATEMENT
        elif "balance sheet" in lower:
            doc_type = FinancialDocSpecificType.BALANCE_SHEET
        elif "cash flow" in lower:
            doc_type = FinancialDocSpecificType.CASHFLOW_STATEMENT
        elif "statement of equity" in lower or "changes in equity" in lower:
            doc_type = FinancialDocSpecificType.STATEMENT_OF_EQUITY
        else:
            doc_type = FinancialDocSpecificType.UNKNOWN

        year_match = re.search(r"\b(19|20)\d{2}\b", text or "")
        doc_year = int(year_match.group(0)) if year_match else -1

        date_match = re.search(r"\b(19|20)\d{2}-\d{2}-\d{2}\b", text or "")
        report_date = date_match.group(0) if date_match else None

        return FinancialDocumentMetadata(
            doc_specific_type=doc_type,
            company_name="",
            report_date=report_date,
            doc_year=doc_year,
            doc_quarter=-1,
            doc_summary=""
        )