# backend/models/audit.py
"""Audit and compliance models"""

from pydantic import BaseModel, Field
from typing import Dict, Optional, Any, Literal
from datetime import datetime

class AuditCertEvent(BaseModel):
    id: str
    entry_id: str
    entry_hash: str
    timestamp: datetime
    event_type: str
    layer: int = Field(..., ge=1, le=10)
    details: Dict[str, Any]
    persona: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    forked_from: Optional[str] = None
    certificate: Optional[Dict[str, Any]] = None

class ComplianceViolation(BaseModel):
    id: str
    type: Literal["CONFIDENCE_LOW", "ENTROPY_HIGH", "CONTAINMENT_BREACH", "DRIFT_DETECTED"]
    layer: int = Field(..., ge=1, le=10)
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    message: str
    timestamp: datetime
    auto_contained: bool = False