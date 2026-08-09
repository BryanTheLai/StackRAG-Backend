from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class CitationPayload(BaseModel):
    document_id: str = Field(..., description="UUID of the cited document")
    filename: str = Field(..., description="Original filename of cited document")
    page: int = Field(1, ge=1, description="Page number of citation")
    excerpt: str = Field(..., description="Relevant text excerpt supporting answer claim")

class ChartDataItem(BaseModel):
    name: str = Field(..., description="Label name for chart item")
    value: Optional[float] = Field(None, description="Numeric value")
    currency: Optional[str] = Field(None, description="Currency unit")

class ChartDataPayload(BaseModel):
    type: str = Field("bar", description="Chart visualization type e.g. bar, line, pie, composed")
    title: str = Field(..., description="Title of visual chart")
    data: List[Dict[str, Any]] = Field(..., description="Chart series data points")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class StructuredAssistantResponse(BaseModel):
    text_answer: str = Field(..., description="Text response content")
    citations: List[CitationPayload] = Field(default_factory=list, description="Claim-grounded citations")
    chart: Optional[ChartDataPayload] = Field(None, description="Optional visual chart data")
    prompt_version: str = Field("v1.2.0-financial-rag", description="Version of prompt used")

class ErrorResponsePayload(BaseModel):
    error_code: str = Field(..., description="Public error code identifier")
    message: str = Field(..., description="User-safe error description")
    request_id: str = Field(..., description="Correlation request ID")
