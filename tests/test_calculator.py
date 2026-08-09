import unittest
from src.llm.tools.calculator import (
    CalculationRequest,
    execute_financial_calculation,
)

class TestFinancialCalculator(unittest.TestCase):

    def test_sum_calculation(self):
        req = CalculationRequest(
            operation="sum",
            values=["1000.50", "2500.25", "500.00"],
            labels=["Q1", "Q2", "Q3"],
            unit="USD"
        )
        res = execute_financial_calculation(req)
        self.assertEqual(res.result, "4000.75")
        self.assertEqual(res.operation, "sum")
        self.assertIn("4000.75 USD", res.explanation)

    def test_difference_calculation(self):
        req = CalculationRequest(
            operation="difference",
            values=["10000.00", "3500.00", "1500.00"],
            labels=["Revenue", "Cost of Goods", "Operating Expenses"],
            unit="USD"
        )
        res = execute_financial_calculation(req)
        self.assertEqual(res.result, "5000.00")
        self.assertEqual(res.formula, "10000.00 - 3500.00 - 1500.00")

    def test_ratio_calculation(self):
        req = CalculationRequest(
            operation="ratio",
            values=["150.00", "50.00"],
            labels=["Current Assets", "Current Liabilities"]
        )
        res = execute_financial_calculation(req)
        self.assertEqual(res.result, "3.0000")

    def test_ratio_division_by_zero(self):
        req = CalculationRequest(
            operation="ratio",
            values=["150.00", "0.00"]
        )
        with self.assertRaises(ValueError):
            execute_financial_calculation(req)

    def test_percentage_change(self):
        req = CalculationRequest(
            operation="percentage_change",
            values=["100.00", "150.00"],
            labels=["2024 Revenue", "2025 Revenue"]
        )
        res = execute_financial_calculation(req)
        self.assertEqual(res.result, "50.00")
        self.assertEqual(res.unit, "%")

    def test_min_max_calculation(self):
        req = CalculationRequest(
            operation="min",
            values=["450.00", "120.00", "980.00"]
        )
        res_min = execute_financial_calculation(req)
        self.assertEqual(res_min.result, "120.00")

        req_max = CalculationRequest(
            operation="max",
            values=["450.00", "120.00", "980.00"]
        )
        res_max = execute_financial_calculation(req_max)
        self.assertEqual(res_max.result, "980.00")

if __name__ == "__main__":
    unittest.main()

