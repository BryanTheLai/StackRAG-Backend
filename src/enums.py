# src/enums.py

from enum import Enum

class DocType(Enum):
    """Enumerates supported document file types."""
    PDF = "pdf"
    DOCX = "docx"
    # Add other types like XLSX, CSV if supported later
    UNKNOWN = "unknown" # Fallback for unsupported types

class FinancialDocSpecificType(Enum):
    """Enumerates specific types of financial documents."""
    # Standard Financial Statements
    BALANCE_SHEET = "Balance Sheet"
    INCOME_STATEMENT = "Income Statement"
    CASHFLOW_STATEMENT = "Cash Flow Statement"
    STATEMENT_OF_EQUITY = "Statement of Equity"

    # Reporting Periods/Types
    ANNUAL_REPORT = "Annual Report"
    QUARTERLY_REPORT = "Quarterly Report"
    MONTHLY_REPORT = "Monthly Report"

    # Other Business Documents
    INVOICE = "Invoice"
    RECEIPT = "Receipt"
    BUDGET = "Budget"
    FORECAST = "Forecast"
    TAX_FILING = "Tax Filing"
    AUDIT_REPORT = "Audit Report"

    # Generic/Catch-all
    GENERAL_REPORT = "General Report"
    STATEMENT = "Statement" # For documents titled "Statement" without more detail
    OTHER = "Other" # If the AI can't classify precisely
    UNKNOWN = "Unknown" # If parsing/extraction fails to identify type

# Note: Enums provide a controlled vocabulary.
# When storing in the database (which uses TEXT columns), we'll store
# the `.value` of the enum member (the string like "pdf" or "Balance Sheet").