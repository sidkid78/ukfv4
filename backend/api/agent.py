from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any # Added List & Any for type hinting agent_db value
from models.agent import AgentCreateRequest
from models.agent import AgentStatus

router = APIRouter(prefix="/agent", tags=["agent"])

# In-memory agents stub (as per Subtask 1 & 7 blueprints)
agent_db: Dict[str, Dict[str, Any]] = {} # Adjusted type hint for value

@router.post("/spawn", response_model=Dict[str, str]) # Explicit response model
def spawn_agent(req: AgentCreateRequest):
    agent_id = f"agent_{len(agent_db) + 1}"
    # Storing more fields as per AgentStatus and typical agent representation
    agent_db[agent_id] = {
        "id": agent_id, # Store id for consistency with AgentStatus
        "name": req.name,
        "role": req.role,
        "persona": req.persona,
        "active": True,
        "context": {},
        # "memory_trace": [] # If agents are to have memory_trace from the start
    }
    return {"agent_id": agent_id}

@router.post("/set_context/{agent_id}", response_model=Dict[str, bool])
def set_agent_context(agent_id: str, context: dict):
    if agent_id not in agent_db:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    if not agent_db[agent_id].get("active", False):
        raise HTTPException(status_code=400, detail=f"Agent {agent_id} is not active")
    agent_db[agent_id]["context"].update(context)
    return {"ok": True}

@router.get("/status/{agent_id}", response_model=AgentStatus)
def get_agent_status(agent_id: str):
    agent_data = agent_db.get(agent_id)
    if not agent_data:
        raise HTTPException(status_code=404, detail="Agent not found")
    # Construct AgentStatus from the stored dict
    return AgentStatus(**agent_data)

@router.get("/all", response_model=List[AgentStatus]) # Return a list of AgentStatus
def list_agents():
    # Convert stored dicts to AgentStatus models
    return [AgentStatus(**data) for data in agent_db.values()]

@router.post("/kill/{agent_id}", response_model=Dict[str, str]) # Explicit response model
def kill_agent(agent_id: str):
    if agent_id not in agent_db:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    agent_db[agent_id]["active"] = False
    return {"status": "killed", "agent_id": agent_id} 