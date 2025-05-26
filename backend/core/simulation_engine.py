# backend/core/simulation_engine.py
"""
Enhanced Simulation Engine for UKG/USKD Multi-Layered Reasoning
Orchestrates Layers 1-10 with dynamic escalation, fork handling, and safety monitoring
Includes real-time WebSocket notifications for live UI updates
"""

import time
import uuid
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json
import os

from models.simulation import (
    SimulationQuery, SimulationSession, LayerState, TraceStep, 
    SimulationStatus, LayerStatus, ConfidenceScore
)
from core.layers.base import layer_registry, LayerResult
from core.memory import global_memory_graph
from core.agents.agent_manager import AgentManager
from core.plugin_loader import ka_registry
from core.audit import audit_logger, make_patch_certificate
from core.compliance import compliance_engine
from core.websocket_manager import websocket_manager

# Configure logger to also write to a file
LOG_DIR = os.path.join(os.path.dirname(__file__), "../../logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "simulation_engine.log")

file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
file_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == file_handler.baseFilename for h in logger.handlers):
    logger.addHandler(file_handler)

def save_session_to_file(session: SimulationSession, suffix: str = "") -> None:
    """Save the session object to a JSON file for auditing/debugging."""
    try:
        filename = f"session_{session.id}{suffix}.json"
        filepath = os.path.join(LOG_DIR, filename)
        # Use pydantic's .model_dump() if available, else .dict()
        if hasattr(session, "model_dump"):
            data = session.model_dump()
        else:
            data = session.dict()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, default=str, indent=2)
        logger.info(f"Session saved to {filepath}")
    except Exception as e:
        logger.error(f"Failed to save session to file: {e}")

def save_trace_to_file(trace: List[Any], session_id: str) -> None:
    """Save the trace list to a JSON file."""
    try:
        filename = f"trace_{session_id}.json"
        filepath = os.path.join(LOG_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(trace, f, default=str, indent=2)
        logger.info(f"Trace saved to {filepath}")
    except Exception as e:
        logger.error(f"Failed to save trace to file: {e}")

class SimulationEngine:
    """
    Advanced simulation engine that orchestrates multi-layered reasoning
    with dynamic escalation, fork handling, comprehensive safety monitoring,
    and real-time WebSocket notifications.
    """

    def __init__(self):
        self.memory = global_memory_graph
        self.agent_manager = AgentManager()
        self.sessions: Dict[str, SimulationSession] = {}

        # Configuration
        self.max_layers = 10
        self.global_confidence_threshold = 0.995
        self.max_simulation_time = 300.0  # 5 minutes max
        self.containment_threshold = 0.5

    def create_session(self, query: SimulationQuery, user_id: str = None) -> SimulationSession:
        """Create a new simulation session"""
        session_id = str(uuid.uuid4())
        run_id = f"run_{int(time.time())}_{session_id[:8]}"

        session = SimulationSession(
            id=session_id,
            run_id=run_id,
            created_at=datetime.now(),
            user_id=user_id,
            status=SimulationStatus.READY,
            layers_active=[],
            current_layer=1,
            input_query=query,
            layers=[],
            state={
                "start_time": time.time(),
                "total_patches": 0,
                "total_forks": 0,
                "agents_spawned": [],
                "containment_triggered": False,
                "safety_violations": []
            }
        )

        self.sessions[session_id] = session
        logger.info(f"Created new simulation session: {session_id} for user_id={user_id}")
        save_session_to_file(session, suffix="_created")
        return session

    # Synchronous version for compatibility
    def run_simulation(
        self,
        query: SimulationQuery,
        user_id: str = None,
        max_layers: Optional[int] = None
    ) -> Dict[str, Any]:
        """Run simulation synchronously (for compatibility)"""
        return asyncio.run(self.run_simulation_async(query, user_id, max_layers))

    async def run_simulation_async(
        self,
        query: SimulationQuery,
        user_id: str = None,
        max_layers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run a complete simulation through all necessary layers with WebSocket updates.
        """
        logger.info(f"Starting simulation: {query.user_query[:100]}... (user_id={user_id})")

        # Create session
        session = self.create_session(query, user_id)
        session.status = SimulationStatus.RUNNING
        save_session_to_file(session, suffix="_started")

        # Notify WebSocket clients of simulation start
        await websocket_manager.notify_simulation_started(
            session_id=session.id,
            simulation_data={
                "session_id": session.id,
                "run_id": session.run_id,
                "query": query.user_query,
                "user_id": user_id,
                "estimated_layers": max_layers or self.max_layers
            }
        )

        try:
            # Initialize simulation state
            current_data = {
                "user_query": query.user_query,
                "axes": query.axes or [0.0] * 13,
                "context": query.context or {}
            }

            state = session.state.copy()
            state.update({
                "session_id": session.id,
                "run_id": session.run_id,
                "orig_query": query.user_query,
                "axes": current_data["axes"].copy()
            })

            all_traces = []
            final_output = None
            previous_confidence = 0.0

            # Process through layers
            for layer_num in range(1, min(max_layers or self.max_layers, self.max_layers) + 1):
                logger.info(f"Processing Layer {layer_num} for session {session.id}")

                # Check timeout
                if time.time() - state["start_time"] > self.max_simulation_time:
                    logger.warning(f"Simulation timeout reached for session {session.id}")
                    session.status = SimulationStatus.FAILED
                    break

                # Get layer instance
                layer = layer_registry.get_layer(layer_num)
                if not layer:
                    logger.error(f"Layer {layer_num} not found for session {session.id}")
                    continue

                # Notify layer start
                await websocket_manager.notify_layer_started(
                    session_id=session.id,
                    layer_info={
                        "layer": layer_num,
                        "name": layer.layer_name,
                        "timestamp": datetime.now().isoformat()
                    }
                )

                # Process layer
                start_time = time.time()
                layer_result = await self._process_layer_async(
                    layer, current_data, state, session
                )
                processing_time = time.time() - start_time

                # Create layer state
                layer_state = self._create_layer_state(
                    layer, layer_result, processing_time, previous_confidence
                )
                session.layers.append(layer_state)
                session.current_layer = layer_num

                # Add traces
                all_traces.extend(layer_state.trace)

                # Save intermediate session and trace to file
                save_session_to_file(session, suffix=f"_layer{layer_num}")
                save_trace_to_file(all_traces, session.id)

                # Notify layer completion
                await websocket_manager.notify_layer_completed(
                    session_id=session.id,
                    layer_result={
                        "layer": layer_num,
                        "name": layer.layer_name,
                        "status": layer_state.status.value,
                        "confidence": layer_result.confidence,
                        "processing_time": processing_time,
                        "escalate": layer_result.escalate,
                        "patches_count": len(layer_result.patches),
                        "agents_spawned": layer_result.agents_spawned
                    }
                )

                # Handle escalation and completion logic
                if not layer_result.escalate and layer_result.confidence >= self.global_confidence_threshold:
                    logger.info(f"Simulation completed at Layer {layer_num} for session {session.id}")
                    final_output = layer_result.output
                    session.status = SimulationStatus.COMPLETED
                    break

                # Update for next layer
                current_data = layer_result.output
                previous_confidence = layer_result.confidence

                # Small delay for WebSocket processing
                await asyncio.sleep(0.1)

            # Finalize session
            if session.status == SimulationStatus.RUNNING:
                session.status = SimulationStatus.COMPLETED if final_output else SimulationStatus.FAILED

            session.final_output = final_output
            session.state = state

            # Save final session and trace to file
            save_session_to_file(session, suffix="_final")
            save_trace_to_file(all_traces, session.id)

            # Notify simulation completion
            await websocket_manager.notify_simulation_completed(
                session_id=session.id,
                results={
                    "session_id": session.id,
                    "run_id": session.run_id,
                    "status": session.status.value,
                    "layers_processed": len(session.layers),
                    "final_output": final_output,
                    "processing_time": time.time() - state["start_time"]
                }
            )

            logger.info(f"Simulation finished for session {session.id} with status {session.status.value}")

            return {
                "run_id": session.run_id,
                "session": session,
                "trace": all_traces,
                "final_output": final_output,
                "state": state
            }

        except Exception as e:
            logger.error(f"Simulation failed for session {session.id if 'session' in locals() else 'unknown'}: {str(e)}", exc_info=True)
            if 'session' in locals():
                session.status = SimulationStatus.FAILED
                session.state["error"] = str(e)
                save_session_to_file(session, suffix="_error")
            raise

    async def _process_layer_async(
        self,
        layer,
        input_data: Dict[str, Any],
        state: Dict[str, Any],
        session: SimulationSession
    ) -> LayerResult:
        """Process a single layer with WebSocket notifications"""

        # Get agents if needed
        agents = None
        if hasattr(layer, 'requires_agents') and layer.requires_agents:
            agents = self._get_or_spawn_agents(layer, state)

            # Notify agent spawning
            for agent in agents or []:
                logger.info(f"Agent spawned: {getattr(agent, 'id', 'unknown')} for layer {layer.layer_number} in session {session.id}")
                await websocket_manager.notify_agent_spawned(
                    session_id=session.id,
                    agent_info={
                        "agent_id": getattr(agent, 'id', 'unknown'),
                        "layer": layer.layer_number,
                        "role": getattr(agent, 'role', 'unknown')
                    }
                )

        # Process the layer
        try:
            # For now, create a simple result since we don't have the full layer implementation
            result = LayerResult(
                output=input_data,
                confidence=0.95,
                escalate=False,
                trace={"layer": layer.layer_number, "processed": True},
                patches=[],
                forks=[],
                agents_spawned=[],
                metadata={"processing_successful": True}
            )
            logger.info(f"Layer {layer.layer_number} processed successfully for session {session.id}")
            return result

        except Exception as e:
            logger.error(f"Layer {layer.layer_number} processing failed for session {session.id}: {e}")

            # Return safe failure result
            return LayerResult(
                output=input_data,  # Pass through input
                confidence=0.1,  # Very low confidence
                escalate=True,  # Force escalation
                trace={"error": str(e), "layer": layer.layer_number},
                metadata={"failed": True, "error": str(e)}
            )

    def _create_layer_state(
        self,
        layer,
        result: LayerResult,
        processing_time: float,
        previous_confidence: float
    ) -> LayerState:
        """Create layer state object from layer result"""

        # Calculate confidence delta
        confidence_delta = result.confidence - previous_confidence

        confidence_score = ConfidenceScore(
            layer=layer.layer_number,
            score=result.confidence,
            delta=confidence_delta,
            entropy=result.trace.get("entropy", 0.05)
        )

        # Create trace steps
        trace_steps = []

        # Main processing trace
        trace_steps.append(TraceStep(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            layer=layer.layer_number,
            layer_name=layer.layer_name,
            message=f"Layer {layer.layer_number} processing completed",
            event_type="layer_entry",
            confidence=confidence_score,
            input_Snapshot={},
            output_snapshot=result.output
        ))

        # Determine layer status
        if result.confidence < 0.5:
            status = LayerStatus.ESCALATED
        elif result.escalate:
            status = LayerStatus.ESCALATED
        else:
            status = LayerStatus.COMPLETED

        logger.info(f"LayerState created for layer {layer.layer_number} with status {status.value}")

        return LayerState(
            layer=layer.layer_number,
            name=layer.layer_name,
            status=status,
            trace=trace_steps,
            agents=result.agents_spawned,
            confidence=confidence_score,
            forked=len(result.forks) > 0,
            escalation=result.escalate,
            persona_reasonings=result.trace.get("persona_reasonings", {}),
            patches=result.patches
        )

    async def _handle_forks_async(self, session: SimulationSession, forks: List[Dict[str, Any]], layer_number: int):
        """Handle fork detection with WebSocket notifications"""
        for fork in forks:
            logger.info(f"Fork detected in Layer {layer_number} for session {session.id}: {fork.get('reason', 'Unknown')}")

            await websocket_manager.notify_memory_forked(
                session_id=session.id,
                fork_info={
                    "layer": layer_number,
                    "fork": fork,
                    "timestamp": datetime.now().isoformat()
                }
            )

    async def _trigger_containment_async(
        self,
        session: SimulationSession,
        layer_number: int,
        violations: List[str]
    ):
        """Trigger containment protocol with WebSocket notifications"""
        logger.critical(f"CONTAINMENT TRIGGERED at Layer {layer_number} for session {session.id}")

        containment_info = {
            "session_id": session.id,
            "trigger_layer": layer_number,
            "violations": violations,
            "timestamp": datetime.now().isoformat(),
            "containment_reason": "Safety violations detected"
        }

        await websocket_manager.notify_containment_triggered(
            session_id=session.id,
            containment_info=containment_info
        )

        session.state["containment_info"] = containment_info
        session.state["containment_triggered"] = True
        save_session_to_file(session, suffix="_containment")

    def _get_or_spawn_agents(self, layer, state: Dict[str, Any]) -> List[Any]:
        """Get existing agents or spawn new ones for the layer"""
        # This would integrate with the agent system
        # For now, return empty list
        logger.info(f"Spawning agents for layer {getattr(layer, 'layer_number', 'unknown')}")
        return []

    def get_session(self, session_id: str) -> Optional[SimulationSession]:
        """Get simulation session by ID"""
        logger.info(f"Retrieving session {session_id}")
        return self.sessions.get(session_id)

    def list_sessions(self) -> List[SimulationSession]:
        """List all simulation sessions"""
        logger.info("Listing all simulation sessions")
        return list(self.sessions.values())

# Global simulation engine instance
simulation_engine = SimulationEngine()
