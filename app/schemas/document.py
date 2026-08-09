from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class DocumentUpload(BaseModel):
    filename: str
    document_type: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    filename: str
    document_type: Optional[str]
    file_size: Optional[int]
    summary: Optional[str]
    key_insights: List[str]
    chunk_count: int
    status: str
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class DocumentQuery(BaseModel):
    question: str
    document_id: Optional[str] = None


class DocumentQueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float


class IntentClassification(BaseModel):
    intent: str
    confidence: float
    complexity: float
    all_scores: Dict[str, float]


class AIResponse(BaseModel):
    response: str
    insights: List[str]
    sources: List[str]
    confidence: float
    follow_up_questions: List[str]
    actions: List[Dict[str, Any]]
    model_used: str
    tokens_used: int
    cost_estimate: float
