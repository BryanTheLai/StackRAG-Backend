# src/enums.py

from enum import Enum

class DocType(Enum):
    """Enumerates supported document file types."""
    PDF = "pdf"
    DOCX = "docx"
    UNKNOWN = "unknown"

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
    STATEMENT = "Statement"
    OTHER = "Other"
    UNKNOWN = "Unknown"