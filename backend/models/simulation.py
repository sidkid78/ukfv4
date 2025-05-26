# backend/models/simulation.py
"""Simulation-related Pydantic models"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime

SimulationLayer = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
SimulationStatus = Literal["READY", "RUNNING", "STEPPING", "COMPLETED", "ESCALATED", "CONTAINED", "FAILED"]
LayerStatus = Literal["READY", "RUNNING", "COMPLETED", "ESCALATED", "CONTAINED"]
EventType = Literal[
    "SIMULATION_START", "LAYER_ENTRY", "LAYER_EXIT", "AGENT_SPAWN", "AGENT_ACTION",
    "MEMORY_PATCH", "FORK_DETECTED", "ESCALATION", "CONTAINMENT", "COMPLIANCE_CHECK", "AUDIT_EVENT"
]

class SimulationQuery(BaseModel):
    user_query: str = Field(..., description="The user's simulation query")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    axes: Optional[List[float]] = Field(default_factory=lambda: [0.0] * 13)

class ConfidenceScore(BaseModel):
    layer: SimulationLayer
    score: float = Field(..., ge=0.0, le=1.0)
    delta: float = Field(default=0.0)
    entropy: Optional[float] = Field(default=None, ge=0.0)

class TraceStep(BaseModel):
    id: str
    timestamp: datetime
    layer: SimulationLayer
    layer_name: str
    message: str
    event_type: EventType
    confidence: ConfidenceScore
    input_snapshot: Dict[str, Any]
    output_snapshot: Dict[str, Any]
    agent: Optional[str] = None
    persona: Optional[str] = None
    notes: Optional[str] = None

class LayerState(BaseModel):
    layer: SimulationLayer
    name: str
    status: LayerStatus
    trace: List[TraceStep] = Field(default_factory=list)
    agents: List[str] = Field(default_factory=list)
    confidence: ConfidenceScore
    forked: bool = False
    escalation: bool = False
    persona_reasonings: Dict[str, str] = Field(default_factory=dict)

class SimulationSession(BaseModel):
    id: str
    run_id: str
    created_at: datetime
    user_id: Optional[str] = None
    status: SimulationStatus
    layers_active: List[SimulationLayer] = Field(default_factory=list)
    current_layer: SimulationLayer = 1
    input_query: SimulationQuery
    layers: List[LayerState] = Field(default_factory=list)
    final_output: Optional[Any] = None
    state: Dict[str, Any] = Field(default_factory=dict)

class SimulationRunResponse(BaseModel):
    run_id: str
    session: SimulationSession
    trace: List[TraceStep]
    final_output: Any
    state: Dict[str, Any]

class LayerStepRequest(BaseModel):
    session_id: str
    target_layer: Optional[SimulationLayer] = None
    steps: int = Field(default=1, ge=1, le=10)
    
class LayerStepResponse(BaseModel):
    layer: SimulationLayer
    status: LayerStatus
    trace: List[TraceStep]
    confidence: ConfidenceScore
    escalation_triggered: bool = False
    patches_applied: List[Any] = Field(default_factory=list)
    agents_spawned: List[str] = Field(default_factory=list)

class SimulationStatus(BaseModel):
    status: SimulationStatus
    layers: List[LayerState]
    final_output: Optional[Any] = None
    state: Dict[str, Any] = Field(default_factory=dict)

class LayerStatus(BaseModel):
    layer: SimulationLayer
    status: LayerStatus
    trace: List[TraceStep]
    confidence: ConfidenceScore
    escalation_triggered: bool = False
    patches_applied: List[Any] = Field(default_factory=list)


