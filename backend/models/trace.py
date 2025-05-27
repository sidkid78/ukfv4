from pydantic import BaseModel, Field
from typing import List, Any, Dict, Optional # Added Optional
import time # For default timestamp

class TraceLogEntry(BaseModel):
    # As per Subtask 1 blueprint for models/trace.py
    layer: int
    layer_name: str
    input_snapshot: Dict[str, Any]
    output_snapshot: Dict[str, Any] # This was Optional in some frontend types, but required here.
    confidence: float
    timestamp: float = Field(default_factory=time.time) # Added default factory
    notes: Optional[str] = "" # Made notes optional as per common usage
    # simulation_id: Optional[str] = None # Could be added if traces are to be associated with a specific sim ID at model level
    # event_type: Optional[str] = None # For more detailed tracing if needed 