# src/services/FinancialDocParser.py

import os
import time
import pymupdf as fitz # Use the official name for PyMuPDF
import concurrent.futures
from typing import Optional, Dict, Any, Tuple, IO
from google.genai import types
# Assuming GeminiClient is in src/llm
from src.llm.GeminiClient import GeminiClient

# Define a simple structure to hold the parsing result
ParsingResult = Dict[str, Any]

class FinancialDocParser:
    """
    Processes financial PDF documents by converting pages to images
    and using a multimodal AI to convert images to structured Markdown.
    Handles file-like objects (buffers) as input.
    Includes specific retry logic for API calls based on original GeminiDoc.
    Wraps each page's content with standard Markdown start/end markers.
    """

    # Prompt for converting PDF images to markdown
    # Adapted from your original prompt for clarity in its role here
    PDF_ANNOTATION_PROMPT = """
    Accurately convert the provided image of a PDF page into GitHub Flavored Markdown.
    Preserve headings, tables, lists, and text formatting precisely.
    Represent tables using Markdown table syntax.
    Do NOT add any extra text, commentary, or markdown block delimiters (```) around the output unless they are part of the image content.
    Focus on accurate 1:1 conversion of the visual layout and text shown in the image.
    """

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """
        Initialize document parser with a Gemini client.
        Uses default GeminiClient if none provided.
        """
        self.gemini_client = gemini_client or GeminiClient()
        # Multimodal models are typically needed for image input
        self.multimodal_model = "gemini-2.0-flash-lite" # Ensure this model supports image input


    def parse_pdf_to_markdown(self, pdf_file: IO[bytes]) -> ParsingResult:
        """
        Processes a PDF file (provided as a buffer/file-like object)
        by converting each page to an image and using Gemini to convert to markdown.

        Args:
            pdf_file: A file-like object (buffer) containing the PDF content in bytes.

        Returns:
            A dictionary containing the combined markdown content and basic info,
            or an error message.
        """
        pdf_document = None # Initialize to None
        try:
            # Use fitz (PyMuPDF) with the file-like object (buffer)
            pdf_document = fitz.open(stream=pdf_file, filetype="pdf")
            total_pages = len(pdf_document)
            print(f"PDF has {total_pages} pages")

            if total_pages == 0:
                 # Ensure document is closed even if no pages
                 if pdf_document:
                    pdf_document.close()
                 return {"markdown_content": "", "page_count": 0, "error": "PDF has no pages."}

            # Pre-render all page images
            pages_data = []
            for page_num in range(total_pages):
                print(f"Rendering page {page_num+1}/{total_pages}")
                page = pdf_document[page_num]
                # Render at a resolution suitable for OCR/analysis (300 DPI equivalent)
                # Matrix (3,3) is commonly used and provides good detail
                pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
                # Convert pixmap to PNG bytes, suitable for AI model input
                img_bytes = pix.tobytes("png")
                # Store data needed for processing each page (0-indexed page_num)
                pages_data.append({"page_num": page_num, "img_bytes": img_bytes})

            # Process pages concurrently with thread pool
            # Limit workers to avoid overwhelming local resources or API limits
            max_workers = min(4, total_pages) # Keep concurrency limited for this simple example
            print(f"Starting page annotation with max {max_workers} concurrent workers...")

            # Using dictionary comprehension for cleaner future tracking
            future_to_page = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                 for page_data in pages_data:
                     future = executor.submit(self._process_single_page, page_data)
                     future_to_page[future] = page_data


            results = [] # List to store processed markdown (or error placeholder) for each page, with page_num
            for future in concurrent.futures.as_completed(future_to_page):
                page_data = future_to_page[future]
                page_num = page_data["page_num"] # Get original page number back (0-indexed)

                try:
                    markdown_result = future.result()
                    results.append((page_num, markdown_result))
                except Exception as exc:
                    print(f'Page {page_num + 1} task failed unexpectedly in executor: {exc}')
                    results.append((page_num, f"\n\n[FATAL ERROR processing Page {page_num+1}: {exc}]\n\n"))


            # Sort results by original page number to reconstruct document order
            results.sort(key=lambda x: x)

            # Combine markdown content wrapping each page with separators
            combined_markdown = ""
            for page_num, markdown_text in results:
                 start_separator = f"\n\n--- Page {page_num+1} Start ---\n\n"
                 end_separator = f"\n\n--- Page {page_num+1} End ---\n\n"
                 combined_markdown += start_separator + markdown_text.strip() + end_separator # strip page text here too

            return {"markdown_content": combined_markdown.strip(), "page_count": total_pages, "error": None}

        except fitz.fitz.FileDataError:
             error_msg = "Error: Could not open PDF file from buffer. File may be corrupt or not a PDF."
             print(error_msg)
             # Return structured error result
             return {"markdown_content": None, "page_count": 0, "error": error_msg}
        except Exception as e:
            # Catch any other unexpected errors during PDF processing (e.g., PyMuPDF issues)
            error_msg = f"An unexpected error occurred during PDF parsing: {str(e)}"
            print(error_msg)
            # Return structured error result
            return {"markdown_content": None, "page_count": 0, "error": error_msg}
        finally:
            # Ensure the PDF document is closed in all cases to free up resources
            if pdf_document:
                pdf_document.close()


    def _process_single_page(self, data: Dict[str, Any]) -> str:
        """
        Processes a single page image with the multimodal Gemini AI,
        including retry logic for common API issues (429, 503), based on original GeminiDoc.
        Returns markdown text for the page or an error placeholder string.
        """
        page_num = data["page_num"] # 0-indexed page number
        img_bytes = data["img_bytes"]
        page_identifier = f"Page {page_num + 1}" # 1-based for print statements and error messages

        max_retries = 5 # Maximum number of retries for API calls
        retry_delay = 10 # seconds to wait before retrying

        # Loop for retries
        for attempt in range(max_retries + 1): # +1 for the initial attempt
            print(f"{page_identifier}: Annotating (Attempt {attempt + 1}/{max_retries + 1})")
            try:
                # Call the AI model using the generate_content method
                # CONTENTS: Pass the image part and the prompt string
                response = self.gemini_client.client.models.generate_content(
                    model=self.multimodal_model,
                    contents=[
                        types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                        self.PDF_ANNOTATION_PROMPT # Pass the prompt string directly
                    ]
                )

                # --- Handle successful response or non-retryable issues ---
                # Check if response has text content
                if hasattr(response, 'text') and response.text:
                    # Basic cleaning: remove potential leading/trailing whitespace
                    processed_text = response.text
                    print(f"{page_identifier}: Annotation successful.")
                    return processed_text # Return the processed text and exit the function

                # Check if response was blocked by safety filters etc.
                elif hasattr(response, 'prompt_feedback') and response.prompt_feedback and hasattr(response.prompt_feedback, 'block_reason'):
                     block_reason = response.prompt_feedback.block_reason
                     print(f"{page_identifier}: Annotation blocked ({block_reason}).")
                     # Return a placeholder indicating the blocked page
                     return f"[Annotation blocked for {page_identifier}: {block_reason}]" # Exit the function

                # Check specifically for RECITATION finish reason as in your original GeminiDoc
                elif hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0 and hasattr(response.candidates, 'finish_reason') and response.candidates.finish_reason == types.GenerateContentResponse.Candidate.FinishReason.RECITATION:
                    print(f"{page_identifier}: Recitation detected - published content not transcribed.")
                    # Return a placeholder indicating recitation was avoided
                    return f"[Warning: {page_identifier}: Recitation of published content avoided.]" # Exit the function

                # Handle other cases where response might not have text but isn't blocked/recitation
                else:
                    print(f"{page_identifier}: Received empty or unexpected AI response format.")
                    # Return an error placeholder for the page
                    return f"[Error processing {page_identifier}: Unexpected AI response.]" # Exit the function


            except Exception as e:
                # --- Handle potential API errors, check if retryable ---
                error_details = str(e)
                # Check for common retryable error indicators in the exception string
                # Added "rate limit" and checked lower case as error messages can vary
                is_retryable = "429" in error_details or "503" in error_details or "rate limit" in error_details.lower()

                if is_retryable and attempt < max_retries:
                    # It's a retryable error and we have retries left
                    print(f"{page_identifier}: Retryable error: {error_details}... Retrying in {retry_delay}s")
                    time.sleep(retry_delay) # Wait before retrying
                    # continue loop to try again (up to max_retries)
                else:
                    # Non-retryable error OR retries exhausted
                    error_msg = f"Failed after {attempt+1} attempts: {error_details}" if is_retryable else f"Non-retryable error: {error_details}"
                    print(f"{page_identifier}: Processing failed - {error_msg}")
                    # Return an error placeholder for the page after failure
                    return f"[Error processing {page_identifier}: {error_msg}]" # Exit the function

        # This part should theoretically not be reached if break/return statements are hit inside the loop
        # But as a final fallback, return an error placeholder if the loop finishes without returning
        print(f"{page_identifier}: Loop finished unexpectedly without returning.")
        return f"[Error: Unknown issue processing {page_identifier} after loop.]"