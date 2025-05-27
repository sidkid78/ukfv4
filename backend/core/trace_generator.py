"""
Trace event generation utilities for UKG/USKD simulation system
Creates detailed trace logs for all simulation activities
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

class TraceEventGenerator:
    """
    Generates structured trace events for simulation activities
    """
    
    def __init__(self):
        self.trace_sequence = 0
    
    def _generate_trace_id(self) -> str:
        """Generate unique trace event ID"""
        self.trace_sequence += 1
        return f"trace_{self.trace_sequence}_{uuid.uuid4().hex[:8]}"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()
    
    def create_simulation_start_event(
        self, 
        session_id: str, 
        user_query: str,
        confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create trace event for simulation start"""
        return {
            "id": self._generate_trace_id(),
            "timestamp": self._get_timestamp(),
            "layer": 1,
            "layer_name": "Simulation Engine",
            "event_type": "simulation_start",
            "message": f"🚀 Simulation started: {user_query[:100]}{'...' if len(user_query) > 100 else ''}",
            "confidence": {
                "layer": 1,
                "score": confidence or 0.0,
                "delta": 0.0,
                "entropy": 0.05
            } if confidence else None,
            "metadata": {
                "session_id": session_id,
                "full_query": user_query,
                "query_length": len(user_query)
            }
        }
    
    def create_layer_entry_event(
        self, 
        layer: int, 
        layer_name: str,
        previous_confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create trace event for layer entry"""
        return {
            "id": self._generate_trace_id(),
            "timestamp": self._get_timestamp(),
            "layer": layer,
            "layer_name": layer_name,
            "event_type": "layer_entry",
            "message": f"📍 Entering Layer {layer}: {layer_name}",
            "metadata": {
                "previous_confidence": previous_confidence,
                "layer_type": "processing"
            }
        }
    
    def create_ai_interaction_event(
        self, 
        layer: int, 
        layer_name: str,
        ai_response: str,
        model: str,
        confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create trace event for AI interaction"""
        response_preview = ai_response[:150] + "..." if len(ai_response) > 150 else ai_response
        
        return {
            "id": self._generate_trace_id(),
            "timestamp": self._get_timestamp(),
            "layer": layer,
            "layer_name": layer_name,
            "event_type": "ai_interaction",
            "message": f"🤖 AI Response ({model}): {response_preview}",
            "confidence": {
                "layer": layer,
                "score": confidence,
                "delta": 0.0,  # Will be calculated later
                "entropy": 0.02
            } if confidence else None,
            "metadata": {
                "model": model,
                "response_length": len(ai_response),
                "full_response": ai_response
            }
        }
    
    def create_confidence_update_event(
        self, 
        layer: int, 
        layer_name: str,
        old_confidence: float,
        new_confidence: float,
        reason: str = "confidence recalculation"
    ) -> Dict[str, Any]:
        """Create trace event for confidence updates"""
        delta = new_confidence - old_confidence
        trend = "📈" if delta > 0 else "📉" if delta < 0 else "➡️"
        
        return {
            "id": self._generate_trace_id(),
            "timestamp": self._get_timestamp(),
            "layer": layer,
            "layer_name": layer_name,
            "event_type": "confidence_update",
            "message": f"{trend} Confidence: {old_confidence:.1%} → {new_confidence:.1%} ({delta:+.1%})",
            "confidence": {
                "layer": layer,
                "score": new_confidence,
                "delta": delta,
                "entropy": abs(delta) * 0.1  # Higher entropy for larger changes
            },
            "metadata": {
                "old_confidence": old_confidence,
                "new_confidence": new_confidence,
                "reason": reason
            }
        }
    
    def create_layer_complete_event(
        self, 
        layer: int, 
        layer_name: str,
        confidence: float,
        escalation: bool = False,
        duration_ms: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create trace event for layer completion"""
        status_icon = "⚠️" if escalation else "✅"
        status_text = "with escalation" if escalation else "successfully"
        duration_text = f" ({duration_ms:.0f}ms)" if duration_ms else ""
        
        return {
            "id": self._generate_trace_id(),
            "timestamp": self._get_timestamp(),
            "layer": layer,
            "layer_name": layer_name,
            "event_type": "layer_complete",
            "message": f"{status_icon} Layer {layer} completed {status_text}{duration_text}",
            "confidence": {
                "layer": layer,
                "score": confidence,
                "delta": 0.0,
                "entropy": 0.05 if escalation else 0.02
            },
            "metadata": {
                "escalation": escalation,
                "duration_ms": duration_ms,
                "final_confidence": confidence
            }
        }
    
    def create_agent_spawn_event(
        self, 
        layer: int, 
        layer_name: str,
        agent_name: str,
        agent_role: str,
        agent_id: str
    ) -> Dict[str, Any]:
        """Create trace event for agent spawning"""
        return {
            "id": self._generate_trace_id(),
            "timestamp": self._get_timestamp(),
            "layer": layer,
            "layer_name": layer_name,
            "event_type": "agent_spawn",
            "message": f"👤 Agent spawned: {agent_name} ({agent_role})",
            "agent": agent_id,
            "metadata": {
                "agent_id": agent_id,
                "agent_name": agent_name,
                "agent_role": agent_role
            }
        }
    
    def create_memory_patch_event(
        self, 
        layer: int, 
        layer_name: str,
        coordinate: List[float],
        operation: str,
        agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create trace event for memory patches"""
        coord_str = f"[{', '.join(f'{x:.2f}' for x in coordinate[:3])}...]"  # Show first 3 coords
        
        return {
            "id": self._generate_trace_id(),
            "timestamp": self._get_timestamp(),
            "layer": layer,
            "layer_name": layer_name,
            "event_type": "memory_patch",
            "message": f"🧠 Memory {operation}: {coord_str}",
            "agent": agent,
            "metadata": {
                "coordinate": coordinate,
                "operation": operation,
                "coordinate_str": coord_str
            }
        }
    
    def create_escalation_event(
        self, 
        layer: int, 
        layer_name: str,
        reason: str,
        next_layer: int,
        confidence: float
    ) -> Dict[str, Any]:
        """Create trace event for escalations"""
        return {
            "id": self._generate_trace_id(),
            "timestamp": self._get_timestamp(),
            "layer": layer,
            "layer_name": layer_name,
            "event_type": "escalation",
            "message": f"⚡ Escalating to Layer {next_layer}: {reason}",
            "confidence": {
                "layer": layer,
                "score": confidence,
                "delta": 0.0,
                "entropy": 0.15  # High entropy for escalations
            },
            "metadata": {
                "reason": reason,
                "next_layer": next_layer,
                "trigger_confidence": confidence
            }
        }
    
    def create_fork_detected_event(
        self, 
        layer: int, 
        layer_name: str,
        fork_reason: str,
        branch_id: str
    ) -> Dict[str, Any]:
        """Create trace event for fork detection"""
        return {
            "id": self._generate_trace_id(),
            "timestamp": self._get_timestamp(),
            "layer": layer,
            "layer_name": layer_name,
            "event_type": "fork_detected",
            "message": f"🌿 Fork detected: {fork_reason}",
            "metadata": {
                "fork_reason": fork_reason,
                "branch_id": branch_id,
                "fork_type": "reasoning_branch"
            }
        }
    
    def create_containment_event(
        self, 
        layer: int, 
        layer_name: str,
        reason: str,
        confidence: float
    ) -> Dict[str, Any]:
        """Create trace event for containment triggers"""
        return {
            "id": self._generate_trace_id(),
            "timestamp": self._get_timestamp(),
            "layer": layer,
            "layer_name": layer_name,
            "event_type": "containment",
            "message": f"🛑 CONTAINMENT TRIGGERED: {reason}",
            "confidence": {
                "layer": layer,
                "score": confidence,
                "delta": 0.0,
                "entropy": 0.5  # Maximum entropy for containment
            },
            "metadata": {
                "containment_reason": reason,
                "trigger_confidence": confidence,
                "severity": "critical"
            }
        }
    
    def create_error_event(
        self, 
        layer: int, 
        layer_name: str,
        error_message: str,
        error_type: str = "simulation_error"
    ) -> Dict[str, Any]:
        """Create trace event for errors"""
        return {
            "id": self._generate_trace_id(),
            "timestamp": self._get_timestamp(),
            "layer": layer,
            "layer_name": layer_name,
            "event_type": "error",
            "message": f"❌ Error: {error_message}",
            "metadata": {
                "error_message": error_message,
                "error_type": error_type
            }
        }

# Global instance
trace_generator = TraceEventGenerator()
