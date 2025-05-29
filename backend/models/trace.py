from pydantic import BaseModel, Field
from typing import List, Any, Dict, Optional
import time

class TraceLogEntry(BaseModel):
    # Updated to match the actual trace data format
    id: Optional[str] = None
    timestamp: str  # Changed from float to string to match ISO format
    layer: int
    layer_name: str
    message: str
    data: Optional[Dict[str, Any]] = None  # Store full event data
    type: Optional[str] = None  # Event type
    agent: Optional[str] = None
    confidence: Optional[float] = None  # Made optional since some events don't have confidence
    entropy: Optional[float] = None
    
    # Legacy fields for backward compatibility
    input_snapshot: Optional[Dict[str, Any]] = None
    output_snapshot: Optional[Dict[str, Any]] = None
    notes: Optional[str] = "" 