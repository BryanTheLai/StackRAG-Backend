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
    # We are being simple and only looking for #, ##, ###, ####, etc.
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
        # Track if we are inside a markdown code block (```) to ignore # inside it
        in_code_block: bool = False

        if not markdown_content:
            print("No markdown content provided to section.")
            return []

        # Split the markdown content into lines for iteration
        lines = markdown_content.splitlines()

        print(f"Sectioning markdown content ({len(lines)} lines)...")

        for line in lines:
            line = line.rstrip() # Remove trailing whitespace

            # Check for markdown code block fences to toggle state
            if line.strip() == "```":
                 in_code_block = not in_code_block
                 current_section_content.append(line) # Include the fence in content
                 continue # Move to the next line

            # Check for page start markers
            page_match = self.PAGE_START_MARKER_PATTERN.match(line)
            if page_match:
                try:
                    page_num_str = page_match.group(1)
                    page_num = int(page_num_str)
                    current_page_numbers.add(page_num)
                except (ValueError):
                    # Handle unexpected marker format - bare bones: just print
                    print(f"Warning: Could not parse page number from marker: {line}")

                # Include the page marker in the current section content (optional, but keeps fidelity)
                current_section_content.append(line)
                continue # Move to the next line

            # Check for Markdown headings, BUT only if NOT inside a code block
            if not in_code_block and self.HEADING_PATTERN.match(line):
                # This line is a new section heading.
                # First, finalize the previous section (if any content has been collected)
                if current_section_content:
                    # Create a dictionary for the finished section
                    section_data: SectionData = {
                        "document_id": document_id,
                        "user_id": user_id,
                        "section_heading": current_section_heading.strip(), # Clean up heading text
                        "page_numbers": sorted(list(current_page_numbers)), # Convert set to sorted list
                        "content_markdown": "\n".join(current_section_content).strip(), # Combine lines and strip whitespace
                        "section_index": section_index_counter,
                        # Add other metadata if needed in the future
                    }
                    sections.append(section_data)
                    print(f"Finalized section {section_index_counter}: '{current_section_heading.strip()}'")
                    section_index_counter += 1

                # Start a new section
                current_section_heading = line.lstrip('# ').strip() # Get the text after the ###
                current_section_content = [line] # Start new content list with the heading line itself
                current_page_numbers = set() # Reset page numbers for the new section
                # Note: The page marker *immediately following* this heading will be added
                # to the *next* section's page numbers when encountered in the loop.

            else:
                # This line is regular content or a page end marker (which we don't need to specifically track)
                # or a code block fence (already handled). Add it to the current section content.
                current_section_content.append(line)


        # After the loop finishes, finalize the very last section
        if current_section_content:
             section_data: SectionData = {
                "document_id": document_id,
                "user_id": user_id,
                "section_heading": current_section_heading.strip(),
                "page_numbers": sorted(list(current_page_numbers)),
                "content_markdown": "\n".join(current_section_content).strip(),
                "section_index": section_index_counter,
             }
             sections.append(section_data)
             print(f"Finalized last section {section_index_counter}: '{current_section_heading.strip()}'")


        print(f"Sectioning complete. Created {len(sections)} sections.")
        return sections