from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import uuid
from datetime import datetime, timezone
import logging
import json

from requests import session

from core.simulation_engine import SimulationEngine as simulation_engine
from models.query import SimulationQuery
from core.gemini_service import gemini_service, GeminiRequest as BackendGeminiRequest, GeminiResponse as BackendGeminiResponse

logger = logging.getLogger(__name__)
# Pydantic equivalent for frontend's SimulationQuery
class BackendSimulationQuery(BaseModel):
    user_query: str
    session_id: str
    context: Optional[Dict[str, Any]] = None
    axes: Optional[List[int]] = None

# Pydantic equivalent for frontend's ConfidenceScore
class BackendConfidenceScore(BaseModel):
    layer: int
    score: float
    delta: float
    entropy: Optional[float] = None

# Pydantic equivalent for frontend's LayerState (simplified)
class BackendLayerState(BaseModel):
    layer: int # SimulationLayer type
    name: str
    status: str # LayerStatus type (e.g., "READY")
    trace: List = [] # Simplified
    agents: List[str] = []
    confidence: BackendConfidenceScore # UPDATED from Dict[str, Any]
    forked: bool = False
    escalation: bool = False
    persona_reasonings: Dict[str, str] = {}
    patches: List = []
    # Add other fields from frontend LayerState as needed
    # For example:
    # confidence: Dict[str, Any] # Simplified, match frontend ConfidenceScore
    # forked: bool = False
    # escalation: bool = False
    # persona_reasonings: Dict[str, str] = {}
    # patches: List = []


# Pydantic equivalent for frontend's SimulationSession
class BackendSimulationSession(BaseModel):
    id: str
    run_id: str
    created_at: str # ISO datetime string
    user_id: Optional[Any] = None
    status: str # SimulationStatus type (e.g., "READY")
    layers_active: List[int] # List of SimulationLayer
    current_layer: int # SimulationLayer
    input_query: BackendSimulationQuery
    layers: List[BackendLayerState] # List of BackendLayerState
    state: Dict[str, Any]
    final_output: Optional[Any] = None
    # Add any other fields from frontend SimulationSession as needed


class BackendStartSimulationResponse(BaseModel): # Mirrors frontend's StartSimulationResponse
    content: str
    model: str
    request_id: str
    session: BackendSimulationSession


router = APIRouter(prefix="/simulation", tags=["simulation"])

run_store = {}

# Add WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connection established for session {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket connection closed for session {session_id}")

    async def send_message(self, session_id: str, message: Dict[str, Any]):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending WebSocket message to session {session_id}: {e}")
                self.disconnect(session_id)

manager = ConnectionManager()

# Add WebSocket endpoint
@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id) # This already calls accept()
    logger.info(f"Test: WebSocket connected for session {session_id}, keeping open.")
    try:
        while True:
            # Just keep it alive, listen for a message or send a ping
            data = await websocket.receive_text()
            logger.info(f"Test: Received data from {session_id}: {data}")
            await websocket.send_text(f"Test: Echo from server for {session_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"Test: WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"Test: WebSocket error for session {session_id}: {e}", exc_info=True)
        manager.disconnect(session_id)

# Modify existing endpoints to use WebSocket for real-time updates
@router.post("/start", response_model=BackendStartSimulationResponse)
async def start_simulation_endpoint(request_data: BackendGeminiRequest):
    try:
        new_session_id = str(uuid.uuid4())
        
        # Create session first so WebSocket can connect
        backend_input_query = BackendSimulationQuery(
            user_query=request_data.prompt,
            session_id=new_session_id,
            context=request_data.context or {},
            axes=request_data.context.get("axes") if request_data.context and isinstance(request_data.context.get("axes"), list) else []
        )
        
        initial_confidence_score = BackendConfidenceScore(
            layer=1,
            score=0.0,
            delta=0.0,
            entropy=None
        )
        
        initial_layer_state = BackendLayerState(
            layer=1,
            name="Layer 1 - Initial Analysis",
            status="READY",
            confidence=initial_confidence_score
        )

        full_session = BackendSimulationSession(
            id=new_session_id,
            run_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            status="INITIALIZING",  # Changed to indicate WebSocket connection can be established
            layers_active=[1],
            current_layer=1,
            input_query=backend_input_query,
            layers=[initial_layer_state],
            state={},
        )
        
        run_store[new_session_id] = full_session.model_dump()

        # Start async processing
        ai_response: BackendGeminiResponse = await gemini_service.generate_async(
            request=request_data,
            session_id=new_session_id
        )

        # Update session status via WebSocket if connected
        full_session.status = "READY"
        run_store[new_session_id] = full_session.model_dump()
        await manager.send_message(new_session_id, {
            "type": "status_update",
            "status": "READY",
            "session": full_session.model_dump()
        })

        return BackendStartSimulationResponse(
            content=ai_response.content,
            model=ai_response.model,
            request_id=ai_response.request_id,
            session=full_session
        )
        
    except Exception as e:
        logger.error(f"Error in /start endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}", response_model=BackendSimulationSession)
async def get_simulation_session(session_id: str):
    """
    Retrieve a specific simulation session by its ID.
    """
    session_data = run_store.get(session_id)
    # ... some other attempts to find session_data if not found directly
    if not session_data:
        raise HTTPException(status_code=404, detail=f"Simulation session with ID '{session_id}' not found.")
    # ...

# Add other endpoints from Subtask 7 blueprint (step, replay, async_start, get_result) later as needed.
