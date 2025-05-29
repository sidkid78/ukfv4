# File: C:\Users\sidki\source\repos\ukfv4\backend\api\layer.py
# New API router for layer timeline and control

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import asyncio
import logging

from core.layer_ka_mapping import layer_ka_manager
from core.websocket_manager import websocket_manager
from api.trace import trace_log_db  # Import the trace database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulation", tags=["layer-control"])

# In-memory simulation state (would be more persistent in production)
simulation_sessions: Dict[str, Dict[str, Any]] = {}
active_websockets: Dict[str, List[WebSocket]] = {}

# Pydantic models for API requests
class LayerStepRequest(BaseModel):
    target_layer: int

class EscalationRequest(BaseModel):
    layer: int
    reason: str

class ContainmentRequest(BaseModel):
    reason: str

class SimulationModeRequest(BaseModel):
    mode: str  # 'AUTO', 'STEPPING', 'MANUAL'

class ControlledRunRequest(BaseModel):
    prompt: str
    max_layer: int = 10
    step_mode: bool = False
    safety_mode: bool = True
    enabled_plugins: List[str] = []

# Layer definitions for display purposes
LAYER_DEFINITIONS = {
    1: {"name": "Simulation Entry", "description": "Query parsing and axis anchoring"},
    2: {"name": "Memory & Knowledge", "description": "Knowledge graph and memory retrieval"},
    3: {"name": "Research Agents", "description": "Multi-agent research and reasoning"},
    4: {"name": "POV Engine", "description": "Point-of-view analysis and triangulation"},
    5: {"name": "Gatekeeper", "description": "Safety validation and consensus building"},
    6: {"name": "Neural Simulation", "description": "Neural network and pattern analysis"},
    7: {"name": "Recursive Reasoning", "description": "Self-referential and meta-cognitive analysis"},
    8: {"name": "Quantum Analysis", "description": "Quantum superposition and multi-reality modeling"},
    9: {"name": "Reality Synthesis", "description": "Consciousness modeling and identity fusion"},
    10: {"name": "Emergence/Containment", "description": "AGI containment and emergence detection"}
}

@router.get("/layers/{session_id}")
async def get_layer_status(session_id: str):
    """Get status of all layers for a simulation session"""
    
    if session_id not in simulation_sessions:
        # Initialize session with default layer states
        simulation_sessions[session_id] = {
            "current_layer": 1,
            "mode": "AUTO",
            "layers": {},
            "created_at": datetime.now().isoformat()
        }
        
        # Initialize trace log for this session
        if session_id not in trace_log_db:
            # Add initial trace entry that matches TraceLogEntry model
            initial_trace = {
                "layer": 1,
                "layer_name": "System",
                "input_snapshot": {"session_id": session_id, "initialized": True},
                "output_snapshot": {"status": "session_initialized", "timestamp": datetime.now().isoformat()},
                "confidence": 1.0,
                "timestamp": datetime.now().timestamp(),
                "notes": "Simulation session initialized"
            }
            trace_log_db[session_id] = [initial_trace]
            
        logger.info(f"Initialized new simulation session: {session_id}")
    
    session = simulation_sessions[session_id]
    layers = []
    
    for layer_num in range(1, 11):
        layer_state = session["layers"].get(str(layer_num), {})
        
        # Get layer definition
        layer_def = LAYER_DEFINITIONS.get(layer_num, {})
        layer_name = layer_def.get("name", f"Layer {layer_num}")
        
        # Get plugins for this layer
        active_plugins = layer_ka_manager.get_kas_for_layer(layer_num)
        
        layer_info = {
            "layer": layer_num,
            "name": layer_name,
            "description": layer_def.get("description", ""),
            "status": layer_state.get("status", "READY"),
            "confidence": layer_state.get("confidence"),
            "processing_time": layer_state.get("processing_time"),
            "escalated": layer_state.get("escalated", False),
            "forked": layer_state.get("forked", False),
            "contained": layer_state.get("contained", False),
            "agents_active": layer_state.get("agents_active", 0),
            "plugins_active": active_plugins,
            "start_time": layer_state.get("start_time"),
            "end_time": layer_state.get("end_time")
        }
        
        layers.append(layer_info)
    
    return layers

@router.post("/step-to-layer/{session_id}")
async def step_to_layer(session_id: str, request: LayerStepRequest):
    """Step simulation to a specific layer"""
    
    if session_id not in simulation_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = simulation_sessions[session_id]
    target_layer = request.target_layer
    current_layer = session.get("current_layer", 1)
    
    if target_layer <= current_layer:
        raise HTTPException(status_code=400, detail="Cannot step backwards")
    
    if target_layer > 10:
        raise HTTPException(status_code=400, detail="Invalid layer number")
    
    # Update session state
    session["current_layer"] = target_layer
    
    # Mark intermediate layers as completed
    for layer_num in range(current_layer, target_layer):
        if str(layer_num) not in session["layers"]:
            session["layers"][str(layer_num)] = {}
        session["layers"][str(layer_num)]["status"] = "COMPLETED"
        session["layers"][str(layer_num)]["end_time"] = datetime.now().isoformat()
    
    # Mark target layer as running
    if str(target_layer) not in session["layers"]:
        session["layers"][str(target_layer)] = {}
    
    session["layers"][str(target_layer)].update({
        "status": "RUNNING",
        "start_time": datetime.now().isoformat(),
        "agents_active": 0 if target_layer < 3 else min(target_layer - 1, 5)
    })
    
    # Notify WebSocket clients
    await notify_layer_change(session_id, "layer_started", {
        "layer": target_layer,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat()
    })
    
    logger.info(f"Session {session_id} stepped to layer {target_layer}")
    
    return {
        "success": True,
        "current_layer": target_layer,
        "message": f"Stepped to layer {target_layer}"
    }

@router.post("/pause/{session_id}")
async def pause_simulation(session_id: str):
    """Pause simulation execution"""
    
    if session_id not in simulation_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = simulation_sessions[session_id]
    session["mode"] = "PAUSED"
    session["paused_at"] = datetime.now().isoformat()
    
    await notify_layer_change(session_id, "simulation_paused", {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat()
    })
    
    logger.info(f"Paused simulation session: {session_id}")
    
    return {"success": True, "mode": "PAUSED"}

@router.post("/resume/{session_id}")
async def resume_simulation(session_id: str):
    """Resume simulation execution"""
    
    if session_id not in simulation_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = simulation_sessions[session_id]
    session["mode"] = "AUTO"
    session["resumed_at"] = datetime.now().isoformat()
    
    await notify_layer_change(session_id, "simulation_resumed", {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat()
    })
    
    logger.info(f"Resumed simulation session: {session_id}")
    
    return {"success": True, "mode": "AUTO"}

@router.post("/escalate/{session_id}")
async def escalate_layer(session_id: str, request: EscalationRequest):
    """Manually escalate a layer"""
    
    if session_id not in simulation_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = simulation_sessions[session_id]
    layer = request.layer
    
    if str(layer) not in session["layers"]:
        session["layers"][str(layer)] = {}
    
    session["layers"][str(layer)]["escalated"] = True
    session["layers"][str(layer)]["escalation_reason"] = request.reason
    session["layers"][str(layer)]["escalation_time"] = datetime.now().isoformat()
    
    await notify_layer_change(session_id, "layer_escalated", {
        "layer": layer,
        "reason": request.reason,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat()
    })
    
    logger.warning(f"Layer {layer} escalated in session {session_id}: {request.reason}")
    
    return {
        "success": True,
        "layer": layer,
        "escalated": True,
        "reason": request.reason
    }

@router.post("/contain/{session_id}")
async def trigger_containment(session_id: str, request: ContainmentRequest):
    """Trigger emergency containment"""
    
    if session_id not in simulation_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = simulation_sessions[session_id]
    current_layer = session.get("current_layer", 1)
    
    # Mark current layer as contained
    if str(current_layer) not in session["layers"]:
        session["layers"][str(current_layer)] = {}
    
    session["layers"][str(current_layer)].update({
        "status": "CONTAINED",
        "contained": True,
        "containment_reason": request.reason,
        "containment_time": datetime.now().isoformat()
    })
    
    session["mode"] = "CONTAINED"
    session["contained_at"] = datetime.now().isoformat()
    
    await notify_layer_change(session_id, "containment_triggered", {
        "layer": current_layer,
        "reason": request.reason,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat()
    })
    
    logger.critical(f"CONTAINMENT TRIGGERED for session {session_id} at layer {current_layer}: {request.reason}")
    
    return {
        "success": True,
        "contained": True,
        "layer": current_layer,
        "reason": request.reason
    }

@router.get("/layer-trace/{session_id}/{layer}")
async def get_layer_trace(session_id: str, layer: int):
    """Get trace information for a specific layer"""
    
    if session_id not in simulation_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = simulation_sessions[session_id]
    layer_state = session["layers"].get(str(layer), {})
    
    # Mock trace data (would come from actual layer execution)
    trace_data = layer_state.get("trace", [
        {
            "id": f"trace_{layer}_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat(),
            "layer": layer,
            "event_type": "layer_started",
            "message": f"Layer {layer} processing initiated",
            "confidence": 0.9,
            "data": {
                "layer_name": LAYER_DEFINITIONS.get(layer, {}).get("name", f"Layer {layer}"),
                "plugins_active": layer_ka_manager.get_kas_for_layer(layer)
            }
        }
    ])
    
    return trace_data

@router.get("/layer-agents/{session_id}/{layer}")
async def get_layer_agents(session_id: str, layer: int):
    """Get active agents for a specific layer"""
    
    if session_id not in simulation_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Mock agent data for layers that use agents
    if layer >= 3:
        agents = [
            {
                "id": f"agent_{layer}_{i}",
                "name": f"Agent {i+1}",
                "persona": ["domain_expert", "critical_thinker", "creative_reasoner", "synthesizer"][i % 4],
                "role": ["RESEARCHER", "ANALYST", "CRITIC", "SYNTHESIZER"][i % 4],
                "status": "active",
                "confidence": 0.8 + (i * 0.05),
                "layer": layer,
                "active": True,
                "context": {},
                "memory_trace": [],
                "created_at": datetime.now().isoformat()
            }
            for i in range(min(layer - 1, 5))
        ]
        return agents
    
    return []

@router.get("/layer-plugins/{session_id}/{layer}")
async def get_layer_plugins(session_id: str, layer: int):
    """Get active plugins for a specific layer"""
    
    # Get plugins from layer-KA mapping
    plugins = layer_ka_manager.get_kas_for_layer(layer)
    
    plugin_details = []
    for plugin_name in plugins:
        config = layer_ka_manager.get_ka_config(plugin_name)
        plugin_details.append({
            "id": plugin_name,
            "name": plugin_name,
            "description": f"Knowledge Algorithm for {plugin_name}",
            "active": True,
            "config": config,
            "layer": layer,
            "type": "KA",
            "version": "1.0.0",
            "layers": [layer],
            "metadata": {
                "layer_specific": True,
                "priority": layer_ka_manager.priority_map.get(plugin_name, 5)
            }
        })
    
    return plugin_details

@router.post("/mode/{session_id}")
async def set_simulation_mode(session_id: str, request: SimulationModeRequest):
    """Set simulation mode (AUTO, STEPPING, MANUAL)"""
    
    if session_id not in simulation_sessions:
        simulation_sessions[session_id] = {
            "current_layer": 1,
            "mode": "AUTO",
            "layers": {},
            "created_at": datetime.now().isoformat()
        }
    
    valid_modes = ["AUTO", "STEPPING", "MANUAL", "PAUSED"]
    if request.mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Invalid mode. Must be one of: {valid_modes}")
    
    old_mode = simulation_sessions[session_id].get("mode", "AUTO")
    simulation_sessions[session_id]["mode"] = request.mode
    simulation_sessions[session_id]["mode_changed_at"] = datetime.now().isoformat()
    
    await notify_layer_change(session_id, "mode_changed", {
        "old_mode": old_mode,
        "new_mode": request.mode,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat()
    })
    
    logger.info(f"Changed simulation mode for session {session_id} from {old_mode} to {request.mode}")
    
    return {"success": True, "mode": request.mode}

@router.post("/run-controlled")
async def run_controlled_simulation(request: ControlledRunRequest):
    """Run simulation with layer control and safety options"""
    
    session_id = f"session_{int(datetime.now().timestamp())}"
    
    # Initialize controlled session
    simulation_sessions[session_id] = {
        "current_layer": 1,
        "mode": "STEPPING" if request.step_mode else "AUTO",
        "max_layer": request.max_layer,
        "safety_mode": request.safety_mode,
        "enabled_plugins": request.enabled_plugins,
        "layers": {},
        "query": request.prompt,
        "started_at": datetime.now().isoformat(),
        "controlled": True
    }
    
    # Initialize first layer
    simulation_sessions[session_id]["layers"]["1"] = {
        "status": "RUNNING",
        "start_time": datetime.now().isoformat(),
        "agents_active": 0,
        "plugins_active": layer_ka_manager.get_kas_for_layer(1)
    }
    
    logger.info(f"Started controlled simulation session: {session_id}")
    
    return {
        "session_id": session_id,
        "mode": "STEPPING" if request.step_mode else "AUTO",
        "max_layer": request.max_layer,
        "message": "Controlled simulation initialized"
    }

@router.get("/state/{session_id}")
async def get_simulation_state(session_id: str):
    """Get complete simulation state"""
    
    if session_id not in simulation_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return simulation_sessions[session_id]

# Helper function to notify WebSocket clients
async def notify_layer_change(session_id: str, event_type: str, data: Dict[str, Any]):
    """Notify WebSocket clients of layer changes"""
    try:
        # Map event types to MessageType enum
        from core.websocket_manager import MessageType
        
        event_mapping = {
            "layer_started": MessageType.LAYER_STARTED,
            "layer_completed": MessageType.LAYER_COMPLETED,
            "layer_escalated": MessageType.LAYER_ESCALATED,
            "simulation_paused": MessageType.SIMULATION_STARTED,  # Use closest match
            "simulation_resumed": MessageType.SIMULATION_STARTED,  # Use closest match
            "containment_triggered": MessageType.CONTAINMENT_TRIGGERED,
            "mode_changed": MessageType.SIMULATION_STARTED  # Use closest match
        }
        
        message_type = event_mapping.get(event_type, MessageType.LAYER_STARTED)
        
        # Use the websocket manager's broadcast method
        await websocket_manager.broadcast_to_session(
            session_id=session_id,
            message_type=message_type,
            data=data
        )
        
    except Exception as e:
        logger.error(f"Failed to notify WebSocket clients: {e}")

# WebSocket endpoint for real-time layer updates
@router.websocket("/ws/layers/{session_id}")
async def layer_websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    # Add to active connections
    if session_id not in active_websockets:
        active_websockets[session_id] = []
    active_websockets[session_id].append(websocket)
    
    logger.info(f"WebSocket connection established for session: {session_id}")
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle client commands
            if message.get("type") == "command":
                command = message.get("command")
                
                if command == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                elif command == "get_status":
                    # Send current session status
                    if session_id in simulation_sessions:
                        session_data = simulation_sessions[session_id]
                        await websocket.send_text(json.dumps({
                            "type": "status_update",
                            "data": session_data,
                            "timestamp": datetime.now().isoformat()
                        }))
                elif command == "subscribe_layer":
                    layer = message.get("data", {}).get("layer")
                    if layer:
                        await websocket.send_text(json.dumps({
                            "type": "layer_subscribed",
                            "data": {"layer": layer},
                            "timestamp": datetime.now().isoformat()
                        }))
                        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
        if session_id in active_websockets:
            active_websockets[session_id].remove(websocket)
            if not active_websockets[session_id]:
                del active_websockets[session_id]
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        if session_id in active_websockets and websocket in active_websockets[session_id]:
            active_websockets[session_id].remove(websocket)
