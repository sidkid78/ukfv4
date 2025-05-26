# backend/models/agent.py
"""Agent and persona related models"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class AgentStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"

class Agent(BaseModel):
    id: str
    name: str
    role: str
    persona: str
    active: bool = True
    status: AgentStatus = AgentStatus.ACTIVE
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

class AgentManager:
    def __init__(self):
        self.agents = {}

    def create_agent(self, agent: AgentCreateRequest) -> Agent:
        new_agent = Agent(**agent.model_dump())
        self.agents[new_agent.id] = new_agent
        return new_agent

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self.agents.get(agent_id)

    def update_agent(self, agent_id: str, update: AgentUpdateRequest) -> Optional[Agent]:
        if agent_id not in self.agents:
            return None
        self.agents[agent_id].update(**update.model_dump())
        return self.agents[agent_id]

    def delete_agent(self, agent_id: str) -> bool:
        if agent_id not in self.agents:
            return False
        del self.agents[agent_id]
        return True
    
    def list_agents(self) -> List[Agent]:
        return list(self.agents.values())
    
    def get_agent_by_persona(self, persona: str) -> Optional[Agent]:
        return next((agent for agent in self.agents.values() if agent.persona == persona), None)

    def get_agent_by_role(self, role: str) -> Optional[Agent]:
        return next((agent for agent in self.agents.values() if agent.role == role), None)

    def get_agent_by_name(self, name: str) -> Optional[Agent]:
        return next((agent for agent in self.agents.values() if agent.name == name), None)
    
    def get_agent_by_id(self, agent_id: str) -> Optional[Agent]:
        return self.agents.get(agent_id)
    
    
