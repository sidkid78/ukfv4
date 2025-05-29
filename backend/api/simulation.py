from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import uuid
from datetime import datetime, timezone
import logging
import json
import os

from core.simulation_engine import simulation_engine
from core.gemini_service import gemini_service, GeminiRequest, GeminiResponse
from core.confidence_calculator import confidence_calculator
from core.trace_generator import trace_generator
from api.trace import trace_log_db  # Import trace storage

# Configure logging to file
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('simulation.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Simple request model for starting simulations
class StartSimulationRequest(BaseModel):
    prompt: str
    context: Optional[Dict[str, Any]] = None

# Simplified response models
class SimulationSessionResponse(BaseModel):
    id: str
    run_id: str
    created_at: str
    status: str
    layers_active: List[int]
    current_layer: int
    input_query: Dict[str, Any]
    layers: List[Dict[str, Any]]
    state: Dict[str, Any]
    final_output: Optional[Any] = None

class StartSimulationResponse(BaseModel):
    content: str
    model: str
    request_id: str
    session: SimulationSessionResponse

router = APIRouter(prefix="/simulation", tags=["simulation"])

# Global session storage
run_store: Dict[str, Dict[str, Any]] = {}

# Helper function to store trace events in trace API database
def store_trace_events(session_id: str, trace_events: List[Dict[str, Any]]):
    """Store trace events in the trace API database"""
    logger.info(f"Storing trace events for session {session_id}")
    if session_id not in trace_log_db:
        trace_log_db[session_id] = []
    
    for event in trace_events:
        # Convert trace event to TraceLogEntry format
        trace_entry = {
            "id": event.get("id", str(uuid.uuid4())),
            "timestamp": event.get("timestamp", datetime.now().isoformat()),
            "layer": event.get("layer", 1),
            "layer_name": event.get("layer_name", "Unknown Layer"),
            "message": event.get("message", ""),
            "data": event,  # Store full event data
            "type": event.get("event_type", "unknown"),
            "agent": event.get("agent"),
            "confidence": event.get("confidence", {}).get("score") if event.get("confidence") else None,
            "entropy": event.get("confidence", {}).get("entropy") if event.get("confidence") else None
        }
        trace_log_db[session_id].append(trace_entry)
    
    logger.info(f"Stored {len(trace_events)} trace events for session {session_id} in database")
    return True

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        # Check if session exists before allowing WebSocket connection
        if session_id not in run_store:
            logger.warning(f"WebSocket connection attempt to invalid session {session_id}")
            await websocket.close(code=4004, reason="Session not found")
            return False
            
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connection established for session {session_id}")
        return True

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket connection closed for session {session_id}")

    async def send_message(self, session_id: str, message: Dict[str, Any]):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
                logger.debug(f"Sent WebSocket message to {session_id}: {json.dumps(message, indent=2)}")
            except Exception as e:
                logger.error(f"Error sending WebSocket message to session {session_id}: {e}")
                self.disconnect(session_id)

manager = ConnectionManager()

# WebSocket endpoint - session must exist first
@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    connected = await manager.connect(websocket, session_id)
    if not connected:
        return
        
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket data from {session_id}: {data[:200]}...")  # Log truncated message
            
            # Echo back for now - extend with real message handling
            await websocket.send_json({
                "type": "echo",
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}", exc_info=True)
        manager.disconnect(session_id)

# Start simulation endpoint - creates session first
@router.post("/start", response_model=StartSimulationResponse)
async def start_simulation(request_data: StartSimulationRequest):
    try:
        # Generate new session ID
        session_id = str(uuid.uuid4())
        run_id = f"run_{int(datetime.now().timestamp())}_{session_id[:8]}"
        
        logger.info(f"Starting simulation with session_id: {session_id}")
        logger.debug(f"Initial request data: {request_data.json()}")
        
        # Create initial session data with trace events
        initial_trace = [
            trace_generator.create_simulation_start_event(
                session_id=session_id,
                user_query=request_data.prompt,
                confidence=0.0  # Will be updated after AI response
            )
        ]
        logger.debug(f"Generated {len(initial_trace)} initial trace events")
        
        session_data = {
            "id": session_id,
            "run_id": run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "INITIALIZING",
            "layers_active": [1],
            "current_layer": 1,
            "input_query": {
                "user_query": request_data.prompt,
                "context": request_data.context or {},
                "session_id": session_id
            },
            "layers": [{
                "layer": 1,
                "name": "Layer 1 - Initial Analysis",
                "status": "READY",
                "trace": initial_trace,
                "agents": [],
                "confidence": {
                    "layer": 1,
                    "score": 0.0,
                    "delta": 0.0,
                    "entropy": 0.05
                },
                "forked": False,
                "escalation": False,
                "persona_reasonings": {},
                "patches": []
            }],
            "state": {
                "created_timestamp": datetime.now().timestamp(),
                "total_patches": 0,
                "total_forks": 0,
                "agents_spawned": [],
                "global_trace": initial_trace
            },
            "final_output": None
        }
        
        # Store session BEFORE any other operations
        run_store[session_id] = session_data
        logger.info(f"Session {session_id} created and stored in run_store")
        logger.debug(f"Initial session data: {json.dumps(session_data, indent=2)}")
        
        # Now make AI request
        gemini_request = GeminiRequest(
            prompt=request_data.prompt,
            context=request_data.context,
            model="gemini-2.5-flash-preview-05-20"
        )
        logger.info(f"Sending request to Gemini service: {gemini_request.model}")
        
        # Process with Gemini
        ai_response = await gemini_service.generate_async(
            request=gemini_request,
            session_id=session_id,
            layer=1
        )
        logger.info(f"Received Gemini response: {ai_response.request_id}")
        logger.debug(f"AI response content: {ai_response.content[:200]}...")
        
        # Calculate confidence based on AI response
        confidence_data = confidence_calculator.calculate_layer_confidence(
            layer_number=1,
            agents_active=0,
            patches_applied=0,
            forks_detected=0,
            escalation_triggered=False,
            ai_response=ai_response.content,
            prompt=request_data.prompt
        )
        logger.info(f"Calculated initial confidence score: {confidence_data['score']}")
        
        # Create trace events for AI interaction and confidence update
        ai_trace_event = trace_generator.create_ai_interaction_event(
            layer=1,
            layer_name="Layer 1 - Initial Analysis",
            ai_response=ai_response.content,
            model=ai_response.model,
            confidence=confidence_data["score"]
        )
        
        confidence_trace_event = trace_generator.create_confidence_update_event(
            layer=1,
            layer_name="Layer 1 - Initial Analysis",
            old_confidence=0.0,
            new_confidence=confidence_data["score"],
            reason="initial AI response analysis"
        )
        
        # Add trace events to layer and global trace
        session_data["layers"][0]["trace"].extend([ai_trace_event, confidence_trace_event])
        session_data["state"]["global_trace"].extend([ai_trace_event, confidence_trace_event])
        logger.debug(f"Added {2} new trace events to layer 1")
        
        # Store trace events in trace API database for UI access
        all_trace_events = session_data["state"]["global_trace"]
        store_trace_events(session_id, all_trace_events)
        
        # Update layer confidence with calculated values
        session_data["layers"][0]["confidence"] = {
            "layer": 1,
            "score": confidence_data["score"],
            "delta": 0.0,
            "entropy": confidence_data["entropy"]
        }
        
        # Update session status
        session_data["status"] = "READY"
        run_store[session_id] = session_data
        logger.info(f"Updated session {session_id} status to READY")
        
        # Notify via WebSocket if connected
        await manager.send_message(session_id, {
            "type": "status_update",
            "status": "READY",
            "session": session_data
        })
        
        # Return response with session info
        return StartSimulationResponse(
            content=ai_response.content,
            model=ai_response.model,
            request_id=ai_response.request_id,
            session=SimulationSessionResponse(**session_data)
        )
        
    except Exception as e:
        logger.error(f"Error in start_simulation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Get session endpoint
@router.get("/session/{session_id}", response_model=SimulationSessionResponse)
async def get_simulation_session(session_id: str):
    """Retrieve a specific simulation session by its ID."""
    logger.info(f"Attempting to retrieve session {session_id}")
    session_data = run_store.get(session_id)
    if not session_data:
        logger.warning(f"Session {session_id} not found in run_store")
        raise HTTPException(
            status_code=404, 
            detail=f"Simulation session with ID '{session_id}' not found."
        )
    logger.info(f"Successfully retrieved session {session_id}")
    return SimulationSessionResponse(**session_data)

# Step simulation endpoint
@router.post("/step/{session_id}")
async def step_simulation(session_id: str):
    """Step the simulation to the next layer."""
    logger.info(f"Processing step request for session {session_id}")
    session_data = run_store.get(session_id)
    if not session_data:
        logger.warning(f"Session {session_id} not found during step request")
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    try:
        # Get current session data for confidence calculation
        current_layers = session_data.get("layers", [])
        previous_confidence = current_layers[-1]["confidence"]["score"] if current_layers else 0.5
        logger.debug(f"Previous confidence score: {previous_confidence}")
        
        # Use the simulation engine to step
        result = simulation_engine.step_simulation(session_id)
        logger.info(f"Simulation engine step result: {json.dumps(result, indent=2)}")
        
        # Calculate confidence for the new layer
        layer_number = result.get("layer", session_data["current_layer"] + 1)
        layer_name = f"Layer {layer_number} - Processing"
        logger.info(f"Processing layer {layer_number}")
        
        # Create trace events for this layer
        trace_events = [
            trace_generator.create_layer_entry_event(
                layer=layer_number,
                layer_name=layer_name,
                previous_confidence=previous_confidence
            )
        ]
        
        confidence_data = confidence_calculator.calculate_layer_confidence(
            layer_number=layer_number,
            agents_active=len(result.get("agents_spawned", [])),
            patches_applied=len(result.get("patches_applied", [])),
            forks_detected=1 if result.get("escalation_triggered", False) else 0,
            escalation_triggered=result.get("escalation_triggered", False),
            ai_response=result.get("content", ""),
            prompt=session_data["input_query"]["user_query"]
        )
        logger.info(f"Calculated new confidence score: {confidence_data['score']}")
        
        # Calculate confidence delta
        confidence_delta = confidence_calculator.calculate_confidence_delta(
            confidence_data["score"], 
            previous_confidence
        )
        logger.debug(f"Confidence delta: {confidence_delta}")
        
        # Add confidence update event if changed
        if confidence_delta != 0:
            trace_events.append(
                trace_generator.create_confidence_update_event(
                    layer=layer_number,
                    layer_name=layer_name,
                    old_confidence=previous_confidence,
                    new_confidence=confidence_data["score"],
                    reason="layer processing"
                )
            )
            logger.debug("Added confidence update trace event")
        
        # Add layer completion event
        trace_events.append(
            trace_generator.create_layer_complete_event(
                layer=layer_number,
                layer_name=layer_name,
                confidence=confidence_data["score"],
                escalation=result.get("escalation_triggered", False)
            )
        )
        logger.info(f"Generated {len(trace_events)} trace events for layer {layer_number}")
        
        # Update stored session
        session_data["current_layer"] = layer_number
        session_data["layers"].append({
            "layer": layer_number,
            "name": layer_name,
            "status": result.get("status", "COMPLETED"),
            "trace": trace_events,
            "agents": result.get("agents_spawned", []),
            "confidence": {
                "layer": layer_number,
                "score": confidence_data["score"],
                "delta": confidence_delta,
                "entropy": confidence_data["entropy"]
            },
            "forked": len(result.get("patches_applied", [])) > 0,
            "escalation": result.get("escalation_triggered", False),
            "persona_reasonings": {},
            "patches": result.get("patches_applied", [])
        })
        
        # Add trace events to global trace
        if "global_trace" not in session_data["state"]:
            session_data["state"]["global_trace"] = []
        session_data["state"]["global_trace"].extend(trace_events)
        
        # Store new trace events in trace API database
        store_trace_events(session_id, trace_events)
        
        run_store[session_id] = session_data
        logger.info(f"Updated session {session_id} with new layer {layer_number} data")
        
        # Notify via WebSocket
        await manager.send_message(session_id, {
            "type": "layer_complete",
            "layer": result
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Error stepping simulation {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# List all sessions
@router.get("/sessions")
async def list_sessions():
    """List all simulation sessions."""
    logger.info("Listing all simulation sessions")
    return list(run_store.values())

# Health check
@router.get("/health")
async def health_check():
    """Check simulation service health."""
    health_status = {
        "status": "healthy",
        "sessions_count": len(run_store),
        "websocket_connections": len(manager.active_connections)
    }
    logger.info(f"Health check: {health_status}")
    return health_status
