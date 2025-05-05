# src/services/Sectioner.py

import re
from typing import List, Dict, Any, Tuple
import uuid # Import uuid for type hinting IDs

# Define a structure for the output of the sectioner
SectionData = Dict[str, Any]

class Sectioner:
    """
    Splits combined document markdown (including page markers)
    into logical sections based on markdown headings.
    """

    # Regex to find Markdown headings (H1 to H6) at the start of a line
    HEADING_PATTERN = re.compile(r'^#+\s.*')

    # Regex to find our custom page start markers
    PAGE_START_MARKER_PATTERN = re.compile(r'^--- Page (\d+) Start ---')

    def __init__(self):
        """Initialize the Sectioner."""
        print("Initialized Sectioner.")
        pass # No complex setup needed for this simple version

    def section_markdown(self, markdown_content: str, document_id: uuid.UUID, user_id: uuid.UUID) -> List[SectionData]:
        """
        Processes the combined markdown content, splitting it into sections.

        Args:
            markdown_content: The full markdown string with page markers.
            document_id: The UUID of the document this markdown belongs to.
            user_id: The UUID of the user who owns the document.

        Returns:
            A list of dictionaries, each representing a section.
        """
        sections: List[SectionData] = []
        current_section_content: List[str] = []
        current_section_heading: str = "Document Start" # Default for content before first heading
        current_page_numbers: set[int] = set()
        section_index_counter: int = 0
        in_code_block: bool = False
        # --- MODIFICATION: Track the last encountered page number ---
        last_page_number_seen: int = 0 # Initialize with 0, page numbers are 1-based

        if not markdown_content:
            print("No markdown content provided to section.")
            return []

        lines = markdown_content.splitlines()

        print(f"Sectioning markdown content ({len(lines)} lines)...")

        for line_index, line in enumerate(lines): # Use line_index for debugging if needed
            line = line.rstrip()

            if line.strip() == "```":
                 in_code_block = not in_code_block
                 current_section_content.append(line)
                 continue

            page_match = self.PAGE_START_MARKER_PATTERN.match(line)
            if page_match:
                try:
                    page_num_str = page_match.group(1)
                    page_num = int(page_num_str)
                    # --- MODIFICATION: Add page number to *current* section's pages ---
                    current_page_numbers.add(page_num)
                    # --- MODIFICATION: Update last page seen ---
                    last_page_number_seen = page_num
                except (ValueError):
                    print(f"Warning: Could not parse page number from marker: {line}")

                current_section_content.append(line)
                continue

            if not in_code_block and self.HEADING_PATTERN.match(line):
                # Found a heading, finalize the previous section first
                if current_section_content:
                    section_data: SectionData = {
                        "document_id": document_id,
                        "user_id": user_id,
                        "section_heading": current_section_heading.strip(),
                        # --- MODIFICATION: Use the pages collected for the *previous* section ---
                        "page_numbers": sorted(list(current_page_numbers)),
                        "content_markdown": "\n".join(current_section_content).strip(),
                        "section_index": section_index_counter,
                    }
                    sections.append(section_data)
                    print(f"Finalized section {section_index_counter}: '{current_section_heading.strip()}' (Pages: {section_data['page_numbers']})") # Added page numbers print
                    section_index_counter += 1

                # Start a new section
                current_section_heading = line.lstrip('# ').strip()
                current_section_content = [line] # Start new content list with the heading line
                # --- MODIFICATION: Initialize new section's pages with the last page seen ---
                current_page_numbers = set()
                if last_page_number_seen > 0: # Only add if a page marker was seen at least once
                    current_page_numbers.add(last_page_number_seen)
                # --- END MODIFICATION ---


            else:
                # Regular content line
                current_section_content.append(line)


        # After the loop finishes, finalize the very last section
        if current_section_content:
             section_data: SectionData = {
                "document_id": document_id,
                "user_id": user_id,
                "section_heading": current_section_heading.strip(),
                "page_numbers": sorted(list(current_page_numbers)), # Use the pages collected for the last section
                "content_markdown": "\n".join(current_section_content).strip(),
                "section_index": section_index_counter,
             }
             sections.append(section_data)
             print(f"Finalized last section {section_index_counter}: '{current_section_heading.strip()}' (Pages: {section_data['page_numbers']})") # Added page numbers print


        print(f"Sectioning complete. Created {len(sections)} sections.")
        return sections