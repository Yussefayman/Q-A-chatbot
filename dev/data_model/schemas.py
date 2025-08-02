from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DocumentChunk(BaseModel):
    """Represents a chunk of text from a document"""
    text: str
    source: str
    chunk_id: int
    metadata: Optional[Dict[str, Any]] = None


class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str] 


class QuestionResponse(BaseModel):
    """Response model for question answers"""
    question: str
    answer: str
    sources: List[str]
    response_time: float
    retrieved_chunks: int
    confidence_score: Optional[float] = None

class DocumentUploadResponse(BaseModel):
    """Response model for document upload"""
    message: str
    document_id: str
    chunks_created: int
    processing_time: float