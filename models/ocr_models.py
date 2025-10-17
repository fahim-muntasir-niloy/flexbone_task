from pydantic import BaseModel


class OCRRequest(BaseModel):
    image_data: bytes


class OCRResponse(BaseModel):
    success: bool
    text: str
    confidence: float
    processing_time_ms: float
