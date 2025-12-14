# src/services/MetadataExtractor.py
from google.genai import types
from src.llm.GeminiClient import GeminiClient
from src.prompts.prompt_manager import PromptManager
from src.models.metadata_models import FinancialDocumentMetadata, IncomeStatementSummaryFields
from src.config.gemini_config import TEXT_MODEL
from src.enums import FinancialDocSpecificType


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
    ) -> tuple[FinancialDocumentMetadata, bool]:
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
        empty_metadata = FinancialDocumentMetadata(
            doc_specific_type=FinancialDocSpecificType.UNKNOWN,
            company_name="",
            report_date=None,
            doc_year=-1,
            doc_quarter=-1,
            doc_summary="",
            total_revenue=None,
            total_expenses=None,
            net_income=None,
            currency=None,
            period_start_date=None,
            period_end_date=None,
        )
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
            if extracted_metadata is not None:
                print("Structured metadata extraction attempted.")
                return extracted_metadata, False

            print(
                "Metadata extraction returned an empty/invalid parsed response (not quota-limited). "
                "Returning empty metadata (UNKNOWN)."
            )
            return empty_metadata, False
        except Exception as e:
            error_text = str(e)
            is_quota = "resource_exhausted" in error_text.lower() or "quota exceeded" in error_text.lower() or "429" in error_text
            if not is_quota:
                raise

        print("Metadata extraction rate-limited (quota). Returning empty metadata (UNKNOWN).")
        return empty_metadata, True

    def extract_income_statement_fields(
        self,
        markdown_text_snippet: str,
        truncate_length: int = 16000,
        original_filename: str | None = None,
    ) -> IncomeStatementSummaryFields | None:
        """Focused LLM extraction for income statement fields only (no heuristics).

        Intended as a second pass when the main metadata extraction did not populate
        required fields for income_statement_summaries.
        """
        truncated = (markdown_text_snippet or "")[:truncate_length]

        filename_hint = (original_filename or "").strip()
        if filename_hint:
            truncated = f"FILENAME: {filename_hint}\n\n" + truncated

        formatted_prompt = PromptManager.get_prompt(
            "income_statement_fields_extraction",
            document_text_snippet=truncated,
        )

        print("Sending text snippet to LLM for income statement fields extraction…")
        try:
            response = self.gemini_client.client.models.generate_content(
                model=self.text_model,
                contents=[formatted_prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=IncomeStatementSummaryFields,
                ),
            )
            fields: IncomeStatementSummaryFields = response.parsed
            if fields:
                print("Income statement fields extraction attempted.")
            return fields
        except Exception as e:
            error_text = str(e)
            is_quota = "resource_exhausted" in error_text.lower() or "quota exceeded" in error_text.lower() or "429" in error_text
            if is_quota:
                print("Income statement fields extraction rate-limited (quota). Skipping second pass.")
                return None
            raise