from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class CalculationRequest(BaseModel):
    operation: str = Field(..., description="Operation type: sum, difference, ratio, percentage_change, min, max")
    values: List[str] = Field(..., description="List of numeric values as strings e.g. ['150000.00', '120000.00']")
    labels: Optional[List[str]] = Field(None, description="Optional labels for input values e.g. ['Revenue Q1', 'Revenue Q2']")
    unit: Optional[str] = Field("USD", description="Currency or unit e.g. USD, MYR, %")

class CalculationResponse(BaseModel):
    operation: str
    result: str
    formula: str
    inputs: List[Dict[str, str]]
    unit: str
    explanation: str

def execute_financial_calculation(request: CalculationRequest) -> CalculationResponse:
    """
    Executes a deterministic financial calculation using Python Decimal arithmetic.
    Never uses unsafe raw string eval or arbitrary code execution.
    """
    if not request.values:
        raise ValueError("Calculation values list cannot be empty.")

    try:
        decimals = [Decimal(v.replace(",", "").strip()) for v in request.values]
    except InvalidOperation as e:
        raise ValueError(f"Invalid numeric input in calculation: {e}")

    op = request.operation.lower().strip()
    labels = request.labels or [f"Value {i+1}" for i in range(len(decimals))]
    inputs_meta = [{"label": labels[i] if i < len(labels) else f"Value {i+1}", "value": str(decimals[i])} for i in range(len(decimals))]

    if op == "sum":
        total = sum(decimals)
        formula = " + ".join([str(d) for d in decimals])
        explanation = f"Sum of {len(decimals)} values is {total} {request.unit}"
        return CalculationResponse(
            operation="sum",
            result=str(total),
            formula=formula,
            inputs=inputs_meta,
            unit=request.unit or "",
            explanation=explanation
        )

    elif op in ("difference", "subtraction"):
        if len(decimals) < 2:
            raise ValueError("Difference operation requires at least 2 values.")
        diff = decimals[0] - sum(decimals[1:])
        formula = f"{decimals[0]} - " + " - ".join([str(d) for d in decimals[1:]])
        explanation = f"Difference is {diff} {request.unit}"
        return CalculationResponse(
            operation="difference",
            result=str(diff),
            formula=formula,
            inputs=inputs_meta,
            unit=request.unit or "",
            explanation=explanation
        )

    elif op == "ratio":
        if len(decimals) != 2:
            raise ValueError("Ratio operation requires exactly 2 values.")
        if decimals[1] == Decimal(0):
            raise ValueError("Division by zero in ratio calculation.")
        ratio = (decimals[0] / decimals[1]).quantize(Decimal("0.0001"))
        formula = f"{decimals[0]} / {decimals[1]}"
        explanation = f"Ratio of {labels[0]} to {labels[1]} is {ratio}"
        return CalculationResponse(
            operation="ratio",
            result=str(ratio),
            formula=formula,
            inputs=inputs_meta,
            unit="",
            explanation=explanation
        )

    elif op == "percentage_change":
        if len(decimals) != 2:
            raise ValueError("Percentage change operation requires exactly 2 values [previous, current].")
        prev, curr = decimals[0], decimals[1]
        if prev == Decimal(0):
            raise ValueError("Base value cannot be zero for percentage change calculation.")
        pct_change = (((curr - prev) / abs(prev)) * Decimal(100)).quantize(Decimal("0.01"))
        formula = f"(({curr} - {prev}) / |{prev}|) * 100"
        explanation = f"Percentage change from {prev} to {curr} is {pct_change}%"
        return CalculationResponse(
            operation="percentage_change",
            result=str(pct_change),
            formula=formula,
            inputs=inputs_meta,
            unit="%",
            explanation=explanation
        )

    elif op == "min":
        min_val = min(decimals)
        formula = f"min({', '.join([str(d) for d in decimals])})"
        explanation = f"Minimum value is {min_val}"
        return CalculationResponse(
            operation="min",
            result=str(min_val),
            formula=formula,
            inputs=inputs_meta,
            unit=request.unit or "",
            explanation=explanation
        )

    elif op == "max":
        max_val = max(decimals)
        formula = f"max({', '.join([str(d) for d in decimals])})"
        explanation = f"Maximum value is {max_val}"
        return CalculationResponse(
            operation="max",
            result=str(max_val),
            formula=formula,
            inputs=inputs_meta,
            unit=request.unit or "",
            explanation=explanation
        )

    else:
        raise ValueError(f"Unsupported calculation operation: '{request.operation}'")
