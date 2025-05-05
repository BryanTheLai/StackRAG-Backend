# src/services/Sectioner.py

import re
from typing import List, Dict, Any
import uuid

SectionData = Dict[str, Any]

class Sectioner:
    """
    Splits markdown content into sections based on headings.
    """

    HEADING_PATTERN = re.compile(r'^#+\s.*')
    PAGE_START_MARKER_PATTERN = re.compile(r'^--- Page (\d+) Start ---')

    def __init__(self):
        """Initialize the Sectioner."""
        print("Initialized Sectioner.")
        pass

    def section_markdown(self, markdown_content: str, document_id: uuid.UUID, user_id: uuid.UUID) -> List[SectionData]:
        """
        Splits markdown content into sections.

        Args:
            markdown_content: Full markdown string.
            document_id: Document UUID.
            user_id: User UUID.

        Returns:
            List of section dictionaries.
        """
        sections: List[SectionData] = []
        current_section_content: List[str] = []
        current_section_heading: str = "Document Start"
        current_page_numbers: set[int] = set()
        section_index_counter: int = 0
        in_code_block: bool = False
        last_page_number_seen: int = 0

        if not markdown_content:
            print("No markdown content provided to section.")
            return []

        lines = markdown_content.splitlines()

        print(f"Sectioning markdown content ({len(lines)} lines)...")

        for line_index, line in enumerate(lines):
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
                    current_page_numbers.add(page_num)
                    last_page_number_seen = page_num
                except (ValueError):
                    print(f"Warning: Could not parse page number from marker: {line}")

                current_section_content.append(line)
                continue

            if not in_code_block and self.HEADING_PATTERN.match(line):
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
                    print(f"Finalized section {section_index_counter}: '{current_section_heading.strip()}' (Pages: {section_data['page_numbers']})")
                    section_index_counter += 1

                current_section_heading = line.lstrip('# ').strip()
                current_section_content = [line]
                current_page_numbers = set()
                if last_page_number_seen > 0:
                    current_page_numbers.add(last_page_number_seen)


            else:
                current_section_content.append(line)


        # Finalize the last section
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
             print(f"Finalized last section {section_index_counter}: '{current_section_heading.strip()}' (Pages: {section_data['page_numbers']})")


        print(f"Sectioning complete. Created {len(sections)} sections.")
        return sections