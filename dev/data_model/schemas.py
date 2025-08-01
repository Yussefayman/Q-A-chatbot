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