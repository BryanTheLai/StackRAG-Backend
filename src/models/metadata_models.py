# src/models/metadata_models.py

from datetime import date # Keep for now, might be used by other models or future changes
from typing import Union, Optional
from pydantic import BaseModel, Field
from src.enums import FinancialDocSpecificType


class IncomeStatementSummaryFields(BaseModel):
    """Subset of fields used to populate income_statement_summaries."""

    total_revenue: Optional[float] = Field(None, description="The total revenue for the period, if applicable.")
    total_expenses: Optional[float] = Field(None, description="The total expenses for the period, if applicable.")
    net_income: Optional[float] = Field(None, description="The net income (profit/loss) for the period, if applicable.")
    currency: Optional[str] = Field(None, description="The 3-letter ISO currency code of the metrics, if applicable.")
    period_start_date: Optional[str] = Field(
        None,
        description="The start date of the reporting period in YYYY-MM-DD format, if applicable.",
        pattern="^\\d{4}-\\d{2}-\\d{2}$"
    )
    period_end_date: Optional[str] = Field(
        None,
        description="The end date of the reporting period in YYYY-MM-DD format, if applicable.",
        pattern="^\\d{4}-\\d{2}-\\d{2}$"
    )

class FinancialDocumentMetadata(BaseModel):
    """
    Structured document metadata. Includes optional core metrics for income statements.
    """
    doc_specific_type: FinancialDocSpecificType = Field(
        ..., description="Specific type of financial report."
    )
    company_name: str = Field(
        "", description="Primary company name."
    )
    # Using Union[str, None] is the modern equivalent of Optional[str]
    report_date: Union[str, None] = Field( # report_date can be None
        None, description="Primary reporting date in YYYY-MM-DD format."
    )
    doc_year: int = Field(
        -1, description="Primary fiscal year."
    )
    doc_quarter: int = Field(
        -1, description="Primary fiscal quarter (1-4). -1 if not quarterly."
    )
    doc_summary: str = Field(
        "", description="Brief summary of the document's content."
    )

    # --- Fields from former IncomeStatementSummary, now optional and part of FinancialDocumentMetadata ---
    total_revenue_calculation: str = Field(None, description="Calculation proof and reasoning for total_revenue_calculation")
    total_revenue: Optional[float] = Field(None, description="The total revenue for the period, if applicable.")

    total_expenses_calculation: str = Field(None, description="Calculation proof and reasoning for total_expenses")
    total_expenses: Optional[float] = Field(None, description="The total expenses for the period, if applicable.")

    net_income_calculation: str = Field(None, description="Calculation proof and reasoning for net_income")
    net_income: Optional[float] = Field(None, description="The final net income (profit/loss) for the period, if applicable.")

    currency: Optional[str] = Field(None, description="The 3-letter ISO currency code of the metrics, if applicable.")
    period_start_date: Optional[str] = Field(
        None,
        description="The start date of the reporting period in YYYY-MM-DD format, if applicable.",
        # Corrected regex pattern
        pattern="^\\d{4}-\\d{2}-\\d{2}$"
    )
    period_end_date: Optional[str] = Field(
        None,
        description="The end date of the reporting period in YYYY-MM-DD format, if applicable.",
        # Corrected regex pattern
        pattern="^\\d{4}-\\d{2}-\\d{2}$"
    )