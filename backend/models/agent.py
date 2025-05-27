# backend/models/agent.py
"""Agent and persona related models"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class Agent(BaseModel):
    id: str
    name: str
    role: str
    persona: str
    active: bool = True
    axes: Optional[List[float]] = Field(default_factory=lambda: [0.0] * 13)
    context: Dict[str, Any] = Field(default_factory=dict)
    memory_trace: List[Any] = Field(default_factory=list)
    created_at: datetime

class AgentCreateRequest(BaseModel):
    name: str
    role: str
    persona: Optional[str] = "default"
    axes: Optional[List[float]] = Field(default_factory=lambda: [0.0] * 13)
    init_prompt: Optional[str] = None

class AgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    persona: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None

class AgentStatus(BaseModel):
    id: str
    name: str
    role: str
    persona: str
    active: bool
    context: Dict[str, Any]
    memory_trace: List[Any]
    created_at: datetime