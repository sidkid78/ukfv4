from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from datetime import datetime, timezone
from models.agent import AgentCreateRequest, AgentStatus

router = APIRouter(prefix="/agent", tags=["agent"])

# In-memory agents storage
agent_db: Dict[str, Dict[str, Any]] = {}

@router.post("/spawn", response_model=AgentStatus)
def spawn_agent(req: AgentCreateRequest):
    agent_id = f"agent_{len(agent_db) + 1}"
    now = datetime.now(timezone.utc)
    
    # Create full agent data with all required fields
    agent_data = {
        "id": agent_id,
        "name": req.name,
        "role": req.role,
        "persona": req.persona or "default",
        "active": True,
        "context": {},
        "memory_trace": [],
        "created_at": now,
    }
    
    agent_db[agent_id] = agent_data
    
    # Return full agent status instead of just ID
    return AgentStatus(**agent_data)

@router.get("/list", response_model=List[AgentStatus])
def list_agents():
    """List all agents with proper typing"""
    return [AgentStatus(**data) for data in agent_db.values()]

@router.get("/all", response_model=List[AgentStatus])
def list_all_agents():
    """Alias for /list endpoint for backward compatibility"""
    return [AgentStatus(**data) for data in agent_db.values()]

@router.delete("/{agent_id}", response_model=Dict[str, str])
def kill_agent(agent_id: str):
    """Delete/kill an agent - using DELETE method for RESTful design"""
    if agent_id not in agent_db:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    agent_db[agent_id]["active"] = False
    return {"status": "killed", "agent_id": agent_id}

@router.post("/kill/{agent_id}", response_model=Dict[str, str])
def kill_agent_post(agent_id: str):
    """Backward compatibility - POST method for killing agents"""
    return kill_agent(agent_id)

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
    
    return AgentStatus(**agent_data)

@router.get("/health")
def agent_health():
    """Health check for agent service"""
    return {
        "status": "healthy",
        "total_agents": len(agent_db),
        "active_agents": len([a for a in agent_db.values() if a.get("active", False)])
    }
