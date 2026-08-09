import unittest
from pydantic import ValidationError
from src.models.chat_models import (
    CitationPayload,
    ChartDataPayload,
    StructuredAssistantResponse,
)

class TestChatModels(unittest.TestCase):

    def test_citation_payload_valid(self):
        cit = CitationPayload(
            document_id="123e4567-e89b-12d3-a456-426614174000",
            filename="Q3_Financials.pdf",
            page=4,
            excerpt="Net revenue increased by 14.2% year-over-year."
        )
        self.assertEqual(cit.page, 4)
        self.assertEqual(cit.filename, "Q3_Financials.pdf")

    def test_citation_payload_invalid_page(self):
        with self.assertRaises(ValidationError):
            CitationPayload(
                document_id="123e4567-e89b-12d3-a456-426614174000",
                filename="Q3_Financials.pdf",
                page=0,
                excerpt="Excerpt..."
            )

    def test_chart_data_payload(self):
        chart = ChartDataPayload(
            type="bar",
            title="Revenue vs Expenses",
            data=[
                {"period": "Q1", "total_revenue": 1000, "total_expenses": 600},
                {"period": "Q2", "total_revenue": 1500, "total_expenses": 800}
            ]
        )
        self.assertEqual(len(chart.data), 2)
        self.assertEqual(chart.type, "bar")

    def test_structured_assistant_response(self):
        resp = StructuredAssistantResponse(
            text_answer="Revenue grew steadily across Q1 and Q2.",
            citations=[
                CitationPayload(
                    document_id="doc-123",
                    filename="Report.pdf",
                    page=1,
                    excerpt="Excerpt text"
                )
            ],
            prompt_version="v1.2.0-financial-rag"
        )
        self.assertEqual(resp.prompt_version, "v1.2.0-financial-rag")
        self.assertEqual(len(resp.citations), 1)

if __name__ == "__main__":
    unittest.main()

