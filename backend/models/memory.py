# backend/models/memory.py
"""Memory and knowledge graph models"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any, Literal, Dict
from datetime import datetime

class MemoryCell(BaseModel):
    coordinate: List[float] = Field(..., min_items=13, max_items=13)
    value: Any
    version: int = 1
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime
    last_modified: datetime

class MemoryPatch(BaseModel):
    id: str
    coordinate: List[float] = Field(..., min_items=13, max_items=13)
    value: Any
    operation: Literal["add", "update", "delete", "fork"]
    source: str
    agent: Optional[str] = None
    persona: Optional[str] = None
    layer: int = Field(..., ge=1, le=10)
    timestamp: datetime
    reason: str
    before: Optional[Any] = None
    after: Optional[Any] = None

class ForkEvent(BaseModel):
    id: str
    parent_layer: int = Field(..., ge=1, le=10)
    fork_layer: int = Field(..., ge=1, le=10)
    reason: str
    agent: str
    timestamp: datetime
    branch_id: str
    confidence_before: float = Field(..., ge=0.0, le=1.0)
    confidence_after: float = Field(..., ge=0.0, le=1.0)