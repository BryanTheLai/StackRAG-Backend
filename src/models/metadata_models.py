# src/models/metadata_models.py

from pydantic import BaseModel, Field
from src.enums import FinancialDocSpecificType

class FinancialDocumentMetadata(BaseModel):
    """Structured document metadata."""
    doc_specific_type: FinancialDocSpecificType = Field(
        ..., description="Specific type of financial report."
    )
    company_name: str = Field(
        ..., description="Primary company name."
    )
    report_date: str # YYYY-MM-DD format
    doc_year: int = Field(
        ..., description="Primary fiscal year."
    )
    doc_quarter: int = Field(
        ..., description="Primary fiscal quarter (1-4). -1 if not quarterly."
    )
    doc_summary: str = Field(
        ..., description="Brief summary."
    )