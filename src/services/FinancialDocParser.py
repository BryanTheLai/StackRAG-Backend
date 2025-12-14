# src/services/FinancialDocParser.py

import time
try:
    import fitz as pymupdf  # type: ignore[import-not-found]  # PyMuPDF canonical import
except Exception:  # pragma: no cover
    import pymupdf  # type: ignore[import-not-found]

try:  # pragma: no cover
    _PYMUPDF_FILE_DATA_ERROR = pymupdf.FileDataError  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    _PYMUPDF_FILE_DATA_ERROR = None
import concurrent.futures
from typing import Optional, Dict, Any, IO
from google.genai import types
from src.llm.GeminiClient import GeminiClient
from src.prompts.prompt_manager import PromptManager
import re
from src.config.gemini_config import MULTIMODAL_MODEL
import os

from src.models.ingestion_models import ParsingResult

class FinancialDocParser:
    """
    Parses PDF financial documents into markdown using a multimodal AI.
    Handles file buffers and includes API retry logic.
    """

    PDF_ANNOTATION_PROMPT = PromptManager.get_prompt(
        "pdf_annotation", pipeline="financial"
    )

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """
        Initialize parser with a Gemini client.
        """
        self.gemini_client = gemini_client or GeminiClient()
        self.multimodal_model = MULTIMODAL_MODEL  # Use model from config


    def parse_pdf_to_markdown(self, pdf_file: IO[bytes]) -> ParsingResult:
        """
        Converts PDF file buffer to combined markdown using Gemini.

        Args:
            pdf_file: PDF content as a file-like object (bytes).

        Returns:
            Dictionary with markdown content, page count, and potential error.
        """
        pdf_document = None
        try:
            # Read PDF buffer into bytes to support SpooledTemporaryFile streams
            pdf_bytes = pdf_file.read()
            pdf_document = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            total_pages = len(pdf_document)
            print(f"PDF has {total_pages} pages")

            disable_gemini_annotation = os.getenv("DISABLE_GEMINI_PDF_ANNOTATION", "0") == "1"

            if total_pages == 0:
                 if pdf_document:
                    pdf_document.close()
                 return {"markdown_content": "", "page_count": 0, "error": "PDF has no pages."}

            if disable_gemini_annotation:
                combined_markdown = self._extract_text_fallback(pdf_document)
                return {"markdown_content": combined_markdown.strip(), "page_count": total_pages, "error": None}

            pages_data = []
            for page_num in range(total_pages):
                print(f"Rendering page {page_num+1}/{total_pages}")
                page = pdf_document[page_num]
                pix = page.get_pixmap(matrix=pymupdf.Matrix(3, 3))
                img_bytes = pix.tobytes("png")
                pages_data.append({"page_num": page_num, "img_bytes": img_bytes})

            max_workers = min(4, total_pages)
            print(f"Starting page annotation with max {max_workers} concurrent workers...")

            future_to_page = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                 for page_data in pages_data:
                     future = executor.submit(self._process_single_page, page_data)
                     future_to_page[future] = page_data


            results = []
            for future in concurrent.futures.as_completed(future_to_page):
                page_data = future_to_page[future]
                page_num = page_data["page_num"]

                try:
                    markdown_result = future.result()
                    results.append((page_num, markdown_result))
                except Exception as exc:
                    print(f'Page {page_num + 1} task failed unexpectedly in executor: {exc}')
                    results.append((page_num, f"\n\n[FATAL ERROR processing Page {page_num+1}: {exc}]\n\n"))


            results.sort(key=lambda x: x[0])

            if any(("resource_exhausted" in (t or "").lower()) or ("quota exceeded" in (t or "").lower()) for _, t in results):
                combined_markdown = self._extract_text_fallback(pdf_document)
                return {"markdown_content": combined_markdown.strip(), "page_count": total_pages, "error": None}

            combined_markdown = ""
            for page_num, markdown_text in results:
                 start_separator = f"\n\n--- Page {page_num+1} Start ---\n\n"
                 end_separator = f"\n\n--- Page {page_num+1} End ---\n\n"
                 combined_markdown += start_separator + markdown_text.strip() + end_separator

            return {"markdown_content": combined_markdown.strip(), "page_count": total_pages, "error": None}

        except Exception as e:
            if _PYMUPDF_FILE_DATA_ERROR is not None and isinstance(e, _PYMUPDF_FILE_DATA_ERROR):
                error_msg = "Error: Could not open PDF file from buffer. File may be corrupt or not a PDF."
                print(error_msg)
                return {"markdown_content": None, "page_count": 0, "error": error_msg}
            error_msg = f"An unexpected error occurred during PDF parsing: {str(e)}"
            print(error_msg)
            return {"markdown_content": None, "page_count": 0, "error": error_msg}
        finally:
            if pdf_document:
                pdf_document.close()


    def _process_single_page(self, data: Dict[str, Any]) -> str:
        """
        Processes a single page image with Gemini, including retry logic.

        Args:
            data: Dictionary containing page_num (0-indexed) and img_bytes.

        Returns:
            Markdown text for the page or an error placeholder string.
        """
        page_num = data["page_num"]
        img_bytes = data["img_bytes"]
        page_identifier = f"Page {page_num + 1}"

        max_retries = 5
        retry_delay = 10

        for attempt in range(max_retries + 1):
            print(f"{page_identifier}: Annotating (Attempt {attempt + 1}/{max_retries + 1})")
            try:
                response = self.gemini_client.client.models.generate_content(
                    model=self.multimodal_model,
                    contents=[
                        types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                        self.PDF_ANNOTATION_PROMPT
                    ]
                )

                if hasattr(response, 'text') and response.text:
                    raw = response.text
                    m = re.search(r"```(?:markdown)?\s*(.*?)\s*```", raw, re.DOTALL)
                    processed_text = m.group(1).strip() if m else raw.strip()
                    print(f"{page_identifier}: Annotation successful.")
                    return processed_text

                elif hasattr(response, 'prompt_feedback') and response.prompt_feedback and hasattr(response.prompt_feedback, 'block_reason'):
                     block_reason = response.prompt_feedback.block_reason
                     print(f"{page_identifier}: Annotation blocked ({block_reason}).")
                     return f"[Annotation blocked for {page_identifier}: {block_reason}]"

                elif hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0 and hasattr(response.candidates, 'finish_reason') and response.candidates.finish_reason == types.GenerateContentResponse.Candidate.FinishReason.RECITATION:
                    print(f"{page_identifier}: Recitation detected - published content not transcribed.")
                    return f"[Warning: {page_identifier}: Recitation of published content avoided.]"

                else:
                    print(f"{page_identifier}: Received empty or unexpected AI response format.")
                    return f"[Error processing {page_identifier}: Unexpected AI response.]"


            except Exception as e:
                error_details = str(e)
                is_quota_exhausted = "resource_exhausted" in error_details.lower() or "quota exceeded" in error_details.lower()
                is_retryable = ("429" in error_details or "503" in error_details or "rate limit" in error_details.lower()) and not is_quota_exhausted

                if is_retryable and attempt < max_retries:
                    print(f"{page_identifier}: Retryable error: {error_details}... Retrying in {retry_delay}s")
                    time.sleep(retry_delay)
                else:
                    error_msg = f"Failed after {attempt+1} attempts: {error_details}" if is_retryable else f"Non-retryable error: {error_details}"
                    print(f"{page_identifier}: Processing failed - {error_msg}")
                    return f"[Error processing {page_identifier}: {error_msg}]"

        print(f"{page_identifier}: Loop finished unexpectedly without returning.")
        return f"[Error: Unknown issue processing {page_identifier} after loop.]"

    def _extract_text_fallback(self, pdf_document: pymupdf.Document) -> str:
        parts: list[str] = []
        total_pages = len(pdf_document)
        for page_num in range(total_pages):
            page = pdf_document[page_num]
            text = (page.get_text("text") or "").strip()
            start_separator = f"\n\n--- Page {page_num+1} Start ---\n\n"
            end_separator = f"\n\n--- Page {page_num+1} End ---\n\n"
            parts.append(start_separator + (text if text else "[No extractable text on this page]") + end_separator)
        return "".join(parts)