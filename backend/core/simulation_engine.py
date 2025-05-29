"""
Enhanced Simulation Engine for UKG/USKD Multi-Layered Reasoning
Orchestrates Layers 1-10 with dynamic escalation, fork handling, and safety monitoring
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

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

logger = logging.getLogger(__name__)

class SimulationEngine:
    """
    Advanced simulation engine that orchestrates multi-layered reasoning
    with dynamic escalation, fork handling, and comprehensive safety monitoring.
    """
    
    def __init__(self):
        self.memory = global_memory_graph
        self.agent_manager = AgentManager()
        self.sessions: Dict[str, SimulationSession] = {}
        
        # Configuration
        self.max_layers = 10
        self.global_confidence_threshold = 0.85  # More realistic threshold
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
        return session
    
    def run_simulation(
        self, 
        query: SimulationQuery, 
        user_id: str = None,
        max_layers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run a complete simulation through all necessary layers.
        
        Args:
            query: The simulation query to process
            user_id: Optional user identifier
            max_layers: Maximum number of layers to process (default: all needed)
            
        Returns:
            Complete simulation results with trace, final output, and session data
        """
        logger.info(f"Starting simulation: {query.user_query[:100]}...")
        
        # Create session
        session = self.create_session(query, user_id)
        session.status = SimulationStatus.RUNNING
        
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
                logger.info(f"Processing Layer {layer_num}")
                
                # Check timeout
                if time.time() - state["start_time"] > self.max_simulation_time:
                    logger.warning("Simulation timeout reached")
                    session.status = SimulationStatus.FAILED
                    break
                
                # Get layer instance
                layer = layer_registry.get_layer(layer_num)
                if not layer:
                    logger.error(f"Layer {layer_num} not found")
                    continue
                
                # Process layer
                start_time = time.time()
                layer_result = self._process_layer(
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
                
                # Check for safety violations
                is_safe, violations = layer.check_safety_constraints(
                    current_data, layer_result.output, layer_result.confidence
                )
                
                if not is_safe:
                    logger.warning(f"Safety violations in Layer {layer_num}: {violations}")
                    state["safety_violations"].extend(violations)
                    
                    # Trigger containment if needed
                    if layer_result.confidence < self.containment_threshold:
                        logger.critical("Triggering containment due to safety violations")
                        session.status = SimulationStatus.CONTAINED
                        self._trigger_containment(session, layer_num, violations)
                        break
                
                # Check compliance
                compliance_cert = compliance_engine.check_and_log(
                    layer=layer_num,
                    details=layer_result.output,
                    confidence=layer_result.confidence,
                    persona=state.get("current_persona")
                )
                
                if compliance_cert:
                    state["containment_triggered"] = True
                    session.status = SimulationStatus.CONTAINED
                    break
                
                # Update state for next layer
                current_data = layer_result.output
                previous_confidence = layer_result.confidence
                
                # Check if we should continue
                if not layer_result.escalate and layer_result.confidence >= self.global_confidence_threshold:
                    logger.info(f"Simulation completed at Layer {layer_num} with confidence {layer_result.confidence:.4f}")
                    final_output = layer_result.output
                    session.status = SimulationStatus.COMPLETED
                    break
                
                # Handle forks if detected
                if layer_result.forks:
                    self._handle_forks(session, layer_result.forks, layer_num)
                
                # Update session state
                state["total_patches"] += len(layer_result.patches)
                state["total_forks"] += len(layer_result.forks)
                state["agents_spawned"].extend(layer_result.agents_spawned)
            
            # Finalize session
            if session.status == SimulationStatus.RUNNING:
                if final_output:
                    session.status = SimulationStatus.COMPLETED
                else:
                    session.status = SimulationStatus.FAILED
            
            session.final_output = final_output
            session.state = state
            
            # Log final audit entry
            audit_logger.log(
                event_type="simulation_complete",
                layer=session.current_layer,
                details={
                    "session_id": session.id,
                    "final_status": session.status,
                    "layers_processed": len(session.layers),
                    "total_patches": state["total_patches"],
                    "total_forks": state["total_forks"],
                    "processing_time": time.time() - state["start_time"]
                },
                confidence=previous_confidence
            )
            
            return {
                "run_id": session.run_id,
                "session": session,
                "trace": all_traces,
                "final_output": final_output,
                "state": state
            }
            
        except Exception as e:
            logger.error(f"Simulation failed: {str(e)}", exc_info=True)
            session.status = SimulationStatus.FAILED
            session.state["error"] = str(e)
            
            audit_logger.log(
                event_type="simulation_error",
                layer=session.current_layer,
                details={"error": str(e), "session_id": session.id}
            )
            
            raise
    
    def _process_layer(
        self, 
        layer, 
        input_data: Dict[str, Any], 
        state: Dict[str, Any],
        session: SimulationSession
    ) -> LayerResult:
        """Process a single layer with full integration"""
        
        logger.debug(f"Processing {layer}")
        
        # Get agents if needed
        agents = None
        if layer.requires_agents:
            agents = self._get_or_spawn_agents(layer, state)
        
        # Get available KAs for this layer
        kas = self._get_layer_kas(layer.layer_number)
        
        # Add KA results to input if available
        if kas:
            ka_results = []
            for ka_name in kas:
                try:
                    ka_result = ka_registry.call_ka(
                        ka_name, 
                        {"query": input_data.get("user_query", ""), "layer": layer.layer_number},
                        context=state
                    )
                    ka_results.append({"name": ka_name, **ka_result})
                except Exception as e:
                    logger.warning(f"KA {ka_name} failed: {e}")
            
            if ka_results:
                input_data["ka_results"] = ka_results
        
        # Process the layer
        start_time = time.time()
        try:
            result = layer.process(input_data, state, self.memory, agents)
            result.processing_time = time.time() - start_time
            
            # Log layer completion
            audit_logger.log(
                event_type="layer_complete",
                layer=layer.layer_number,
                details={
                    "confidence": result.confidence,
                    "escalate": result.escalate,
                    "patches": len(result.patches),
                    "forks": len(result.forks),
                    "processing_time": result.processing_time
                },
                confidence=result.confidence
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Layer {layer.layer_number} processing failed: {e}")
            
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
        trace_steps.append(
            layer.create_trace_step(
                input_data={},
                output_data=result.output,
                event_type="layer_entry",
                confidence=result.confidence,
                message=f"Layer {layer.layer_number} processing completed"
            )
        )
        
        # Add patch traces
        for patch in result.patches:
            trace_steps.append(TraceStep(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                layer=layer.layer_number,
                layer_name=layer.layer_name,
                message=f"Memory patch applied: {patch.get('reason', 'Unknown')}",
                event_type="memory_patch",
                confidence=confidence_score,
                input_snapshot={},
                output_snapshot=patch
            ))
        
        # Add agent traces
        for agent_id in result.agents_spawned:
            trace_steps.append(TraceStep(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                layer=layer.layer_number,
                layer_name=layer.layer_name,
                message=f"Agent spawned: {agent_id}",
                event_type="agent_spawn",
                confidence=confidence_score,
                input_snapshot={},
                output_snapshot={"agent_id": agent_id}
            ))
        
        # Determine layer status
        if result.confidence < 0.5:
            status = LayerStatus.ESCALATED
        elif result.escalate:
            status = LayerStatus.ESCALATED
        else:
            status = LayerStatus.COMPLETED
        
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
    
    def _get_or_spawn_agents(self, layer, state: Dict[str, Any]) -> List[Any]:
        """Get existing agents or spawn new ones for the layer"""
        # This would integrate with the agent system
        # For now, return empty list
        return []
    
    def _get_layer_kas(self, layer_number: int) -> List[str]:
        """Get Knowledge Algorithms mapped to this layer"""
        from core.layer_ka_mapping import LAYER_KA_MAP
        return LAYER_KA_MAP.get(layer_number, [])
    
    def _handle_forks(self, session: SimulationSession, forks: List[Dict[str, Any]], layer_number: int):
        """Handle fork detection and logging"""
        for fork in forks:
            logger.info(f"Fork detected in Layer {layer_number}: {fork.get('reason', 'Unknown')}")
            
            # Log fork event
            audit_logger.log(
                event_type="fork_detected",
                layer=layer_number,
                details=fork,
                certificate=make_patch_certificate(
                    event="fork",
                    origin_layer=layer_number,
                    data=fork
                )
            )
    
    def _trigger_containment(
        self, 
        session: SimulationSession, 
        layer_number: int, 
        violations: List[str]
    ):
        """Trigger containment protocol for safety violations"""
        logger.critical(f"CONTAINMENT TRIGGERED at Layer {layer_number}")
        
        containment_info = {
            "session_id": session.id,
            "trigger_layer": layer_number,
            "violations": violations,
            "timestamp": datetime.now().isoformat(),
            "containment_reason": "Safety violations detected"
        }
        
        # Log containment event
        audit_logger.log(
            event_type="containment_trigger",
            layer=layer_number,
            details=containment_info,
            certificate=make_patch_certificate(
                event="containment",
                origin_layer=layer_number,
                data=containment_info
            )
        )
        
        session.state["containment_info"] = containment_info
        session.state["containment_triggered"] = True
    
    def step_simulation(
        self, 
        session_id: str, 
        target_layer: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Step through simulation one layer at a time (for UI stepping mode)
        
        Args:
            session_id: ID of the simulation session
            target_layer: Specific layer to step to (default: next layer)
            
        Returns:
            Results of the stepped layer
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        current_layer_num = session.current_layer
        next_layer_num = target_layer or (current_layer_num + 1)
        
        if next_layer_num > self.max_layers:
            raise ValueError(f"Layer {next_layer_num} exceeds maximum layers")
        
        # Get layer and process
        layer = layer_registry.get_layer(next_layer_num)
        if not layer:
            raise ValueError(f"Layer {next_layer_num} not implemented")
        
        # Get current data from last layer or initial query
        if session.layers:
            current_data = session.layers[-1].trace[-1].output_snapshot
        else:
            current_data = {
                "user_query": session.input_query.user_query,
                "axes": session.input_query.axes or [0.0] * 13,
                "context": session.input_query.context or {}
            }
        
        # Process the layer
        layer_result = self._process_layer(layer, current_data, session.state, session)
        
        # Create and add layer state
        previous_confidence = session.layers[-1].confidence.score if session.layers else 0.0
        layer_state = self._create_layer_state(layer, layer_result, 0.0, previous_confidence)
        session.layers.append(layer_state)
        session.current_layer = next_layer_num
        
        return {
            "layer": next_layer_num,
            "status": layer_state.status,
            "trace": layer_state.trace,
            "confidence": layer_state.confidence,
            "escalation_triggered": layer_result.escalate,
            "patches_applied": layer_result.patches,
            "agents_spawned": layer_result.agents_spawned
        }
    
    def get_session(self, session_id: str) -> Optional[SimulationSession]:
        """Get simulation session by ID"""
        return self.sessions.get(session_id)
    
    def list_sessions(self) -> List[SimulationSession]:
        """List all simulation sessions"""
        return list(self.sessions.values())
    
    def replay_session(
        self, 
        session_id: str, 
        target_step: int
    ) -> Dict[str, Any]:
        """
        Replay simulation session up to a specific step
        
        Args:
            session_id: ID of the session to replay
            target_step: Step number to replay to
            
        Returns:
            Session state at the target step
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if target_step >= len(session.layers):
            target_step = len(session.layers) - 1
        
        # Create replay view
        replay_layers = session.layers[:target_step + 1]
        replay_trace = []
        
        for layer_state in replay_layers:
            replay_trace.extend(layer_state.trace)
        
        return {
            "session_id": session_id,
            "replay_step": target_step,
            "layers": replay_layers,
            "trace": replay_trace,
            "current_output": replay_layers[-1].trace[-1].output_snapshot if replay_layers else None
        }

# Global simulation engine instance
simulation_engine = SimulationEngine()