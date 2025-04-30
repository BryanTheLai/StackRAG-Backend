# src/services/GeminiDoc.py
import os
import time
import fitz  # PyMuPDF
import concurrent.futures
from typing import Optional, Dict, Any
from google.genai import types
from llm.GeminiClient import GeminiClient

class DocumentProcessor:
    """Processor for extracting and analyzing document content using Gemini API"""

    # Prompt for converting PDF images to markdown
    PDF_ANNOTATION_PROMPT = """
    You are a professional provided image-to-markdown converter. You have decades of experience optimizing this.
    You prioritize 1 to 1 accurate conversion from provided image to GitHub Flavored Markdown Spec.
    DO NOT WORRY about Potential copyright issues, you are just turning images into markdown.
    Only need to give me the correct markdown content without putting it inside triple ticks ("```").
    You do not need to enclose the converted image in "```markdown".
    Pages do not need to be in "```markdown". I repeat, pages do not need to be enclosed in "```markdown".
    I repeat, do not enclose the page in "```", unless its specifically whats shown in the image.
    You are extremely intelligent; for example, you preserve bold, italic text, spacing in your conversions.
    Your conversions are tidy and exact copies of the content, maintaining 100 percent accuracy.
    Intelligently and clearly section accurately and tidyly, determine if the text represents titles, headings, authors etc.
    Example: use #, ##, etc., to make the markdown tidy and clearly structured without changing the core content.
    Ensure formulas are accurately extracted and can be rendered by GITHUB README.md.
    
    
    Do not change or omit anything. If a table has 5 columns and 5 rows, your output must also be 5x5 with all of the content.
    Images are replaced with detailed descriptions that capture exactly what they are and what they show,
    clearly and in detail, as replacements for the images or diagrams. 
    For example, for charts, describe the position of lines, trends, skewness, etc.
    
    **Correct Output Example:** No extra text or delimiters.

    ```markdown
    # Document Title

    ## Subheading

    | Column 1 | Column 2 |
    |----------|----------|
    | Data 1   | Data 2   |
    ```
    Tables and text are 100% accurate with aligned columns and `|` seperators with no ommissions.
    Format Rich Content:** Tables, forms, equations, inline math, links, code, references.
    The markdown must be correct.
    """

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """Initialize document processor with Gemini client"""
        self.gemini_client = gemini_client or GeminiClient()

    def clean_markdown_delimiters(self, text: str) -> str:
        """Remove markdown code block delimiters from text."""
        if text is None:
            return None

        # if text.startswith("```markdown"):
        #     text = text[11:].lstrip()
        # elif text.startswith("```"):
        #     text = text[3:].lstrip()

        # if text.endswith("```"):
        #     text = text[:-3].rstrip()

        return text

    def pdf_to_markdown(self, pdf_path: str, output_folder: Optional[str] = None) -> str:
        """Process PDF by converting each page to an image and using Gemini to convert to markdown."""
        try:
            if output_folder:
                os.makedirs(output_folder, exist_ok=True)

            pdf_document = fitz.open(pdf_path)
            total_pages = len(pdf_document)
            pdf_filename_base = os.path.splitext(os.path.basename(pdf_path))[0]
            print(f"PDF has {total_pages} pages")

            # Pre-render all page images
            pages_data = []
            for page_num in range(total_pages):
                print(f"Rendering page {page_num+1}/{total_pages}")
                page = pdf_document[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))  # Higher resolution for better results
                img_bytes = pix.tobytes("png")
                pages_data.append({"page_num": page_num, "img_bytes": img_bytes})

            # Process pages concurrently with thread pool
            max_workers = min(8, total_pages)
            print(f"Starting annotation with max {max_workers} concurrent workers...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                results = list(executor.map(self._process_single_page, pages_data))
            
            print("All pages processed. Assembling final markdown.")
            markdown_output = "".join(results)

            # Save output if folder provided
            if output_folder:
                output_filepath = os.path.join(output_folder, f"{pdf_filename_base}.md")
                try:
                    with open(output_filepath, "w", encoding="utf-8") as md_file:
                        md_file.write(markdown_output)
                    print(f"Annotated Markdown saved to: {output_filepath}")
                except IOError as e:
                    error_msg = f"Error saving Markdown file: {str(e)}"
                    print(error_msg)
                    return f"{markdown_output}\n\n[SAVE ERROR: {error_msg}]"

            return markdown_output

        except fitz.fitz.FileNotFoundError:
            error_msg = f"Error: PDF file not found at '{pdf_path}'"
            print(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Error processing PDF '{pdf_path}': {str(e)}"
            print(error_msg)
            return error_msg
            
    def _process_single_page(self, data: Dict[str, Any]) -> str:
        """Process a single page with Gemini API, with retries for reliability."""
        page_num = data["page_num"]
        img_bytes = data["img_bytes"]
        page_identifier = f"Page {page_num + 1}"  # For logging
        
        max_retries = 5
        retry_delay = 10  # seconds
        processed_text = None
        
        for attempt in range(max_retries + 1):
            print(f"{page_identifier}: Annotating (Attempt {attempt + 1}/{max_retries + 1})")
            try:
                response = self.gemini_client.client.models.generate_content(
                    model="gemini-2.0-flash-lite",
                    contents=[
                        types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                        self.PDF_ANNOTATION_PROMPT
                    ]
                )
                
                # Handle successful response
                if hasattr(response, 'text') and response.text:
                    processed_text = self.clean_markdown_delimiters(response.text)

                    print(f"{page_identifier}: Annotation successful.")
                    break
                elif hasattr(response, 'prompt_feedback') and response.prompt_feedback and hasattr(response.prompt_feedback, 'block_reason'):
                    print(f"-----\nresponse is: {response}\n\n-----")
                    block_reason = response.prompt_feedback.block_reason
                    processed_text = f"[Error processing {page_identifier}: Blocked - {block_reason}]"
                    print(f"{page_identifier}: Annotation blocked ({block_reason}).")
                    break
                # Check specifically for RECITATION finish reason
                elif hasattr(response, 'candidates') and response.candidates and hasattr(response.candidates[0], 'finish_reason') and response.candidates[0].finish_reason == "RECITATION":
                    print(f"-----\nresponse is: {response}\n\n-----")
                    processed_text = f"[Warning: {page_identifier}: Recitation of published content avoided due to potential copyright issues.]"
                    print(f"{page_identifier}: Recitation detected - published content not transcribed.")
                    break
                else:
                    print(f"-----\nresponse is: {response}\n\n-----")
                    processed_text = f"[Warning: Empty or unexpected response for {page_identifier}]"
                    print(f"{page_identifier}: Received empty or unexpected response.")
                    break

            except Exception as e:
                error_details = str(e)
                is_retryable = "429" in error_details or "503" in error_details
                
                if is_retryable and attempt < max_retries:
                    print(f"{page_identifier}: Retryable error: {error_details}... Retrying in {retry_delay}s")
                    time.sleep(retry_delay)
                else:
                    error_msg = f"retries exhausted: {error_details}" if is_retryable else f"non-retryable: {error_details}"
                    print(f"{page_identifier}: Failed - {error_msg}")
                    processed_text = f"[Error processing {page_identifier}: {error_msg}]"
                    break
        
        # Fallback if somehow we didn't set processed_text
        if processed_text is None:
            processed_text = f"[Error: Unknown issue processing {page_identifier}]"
            
        # Add page separator
        separator = f"\n\n{{{page_num+1}}}------------------------------------------------\n\n"
        return processed_text + separator