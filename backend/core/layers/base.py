# backend/core/layers/base.py
"""
Base layer interface and utilities for UKG/USKD simulation engine
Provides the foundation for all 10 simulation layers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid
import time
import logging

from models.simulation import ConfidenceScore, TraceStep, EventType, SimulationLayer
from core.memory import InMemoryKnowledgeGraph
from core.audit import audit_logger, make_patch_certificate
from core.compliance import compliance_engine

logger = logging.getLogger(__name__)

class LayerResult:
    """Encapsulates the result of a layer processing operation"""
    
    def __init__(
        self,
        output: Dict[str, Any],
        confidence: float,
        escalate: bool = False,
        trace: Dict[str, Any] = None,
        patches: List[Dict[str, Any]] = None,
        forks: List[Dict[str, Any]] = None,
        agents_spawned: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        self.output = output
        self.confidence = confidence
        self.escalate = escalate
        self.trace = trace or {}
        self.patches = patches or []
        self.forks = forks or []
        self.agents_spawned = agents_spawned or []
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.processing_time = 0.0

class BaseLayer(ABC):
    """
    Abstract base class for all simulation layers.
    Provides common functionality and enforces layer interface.
    """
    
    def __init__(self):
        self.layer_number: SimulationLayer = 1
        self.layer_name: str = "BaseLayer"
        self.confidence_threshold: float = 0.995
        self.entropy_threshold: float = 0.1
        self.max_processing_time: float = 30.0  # seconds
        self.requires_agents: bool = False
        self.requires_memory: bool = True
        self.safety_critical: bool = False
        
    @abstractmethod
    def process(
        self,
        input_data: Dict[str, Any],
        state: Dict[str, Any],
        memory: InMemoryKnowledgeGraph,
        agents: Optional[List[Any]] = None
    ) -> LayerResult:
        """
        Process input through this layer's reasoning logic.
        
        Args:
            input_data: Data from previous layer or initial query
            state: Current simulation state and context
            memory: In-memory knowledge graph
            agents: Available agents for this layer
            
        Returns:
            LayerResult containing output, confidence, escalation decision, etc.
        """
        pass
    
    def should_escalate(
        self, 
        confidence: float, 
        entropy: Optional[float] = None,
        context: Dict[str, Any] = None
    ) -> bool:
        """
        Determine if this layer should escalate to the next layer.
        
        Args:
            confidence: Current confidence score
            entropy: Current entropy level
            context: Additional context for escalation decision
            
        Returns:
            True if escalation is needed
        """
        # Base escalation logic
        if confidence < self.confidence_threshold:
            return True
            
        if entropy and entropy > self.entropy_threshold:
            return True
            
        # Layer-specific escalation logic can override this
        return False
    
    def calculate_confidence(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> float:
        """
        Calculate confidence score for this layer's output.
        Base implementation - layers should override for specific logic.
        """
        # Default confidence calculation
        base_confidence = 0.9
        
        # Adjust based on data completeness
        if not output_data or not input_data:
            base_confidence *= 0.5
            
        # Adjust based on processing context
        if context:
            if context.get("ambiguity_detected", False):
                base_confidence *= 0.8
            if context.get("conflict_detected", False):
                base_confidence *= 0.7
                
        return min(1.0, max(0.0, base_confidence))
    
    def calculate_entropy(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> float:
        """
        Calculate entropy/uncertainty for this layer's processing.
        """
        base_entropy = 0.05
        
        # Increase entropy for complex or ambiguous inputs
        if isinstance(input_data.get("query"), str):
            query_length = len(input_data["query"])
            if query_length > 500:
                base_entropy += 0.02
                
        return min(1.0, max(0.0, base_entropy))
    
    def create_trace_step(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        event_type: EventType,
        confidence: float,
        message: str,
        metadata: Dict[str, Any] = None
    ) -> TraceStep:
        """Create a trace step for audit logging"""
        
        return TraceStep(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            layer=self.layer_number,
            layer_name=self.layer_name,
            message=message,
            event_type=event_type,
            confidence=ConfidenceScore(
                layer=self.layer_number,
                score=confidence,
                delta=0.0,  # Will be calculated by engine
                entropy=self.calculate_entropy(input_data, output_data)
            ),
            input_snapshot=input_data,
            output_snapshot=output_data,
            notes=str(metadata or {})
        )
    
    def patch_memory(
        self,
        memory: InMemoryKnowledgeGraph,
        coordinate: List[float],
        value: Any,
        operation: str = "update",
        reason: str = None,
        persona: str = None
    ) -> Dict[str, Any]:
        """
        Apply a memory patch and log it for audit.
        
        Args:
            memory: Knowledge graph to patch
            coordinate: 13D coordinate for the patch
            value: New value to store
            operation: Type of operation (add, update, delete, fork)
            reason: Reason for the patch
            persona: Persona making the patch
            
        Returns:
            Patch information for trace logging
        """
        # Get current value for before/after tracking
        current_cell = memory.get(coordinate, persona=persona)
        before_value = current_cell.get("value") if current_cell else None
        
        # Apply the patch
        if operation == "delete":
            memory.delete(coordinate)
        else:
            memory.patch(
                coordinate=coordinate,
                value=value,
                meta={
                    "layer": self.layer_number,
                    "reason": reason or f"Layer {self.layer_number} processing",
                    "persona": persona or "system",
                    "timestamp": datetime.now().isoformat()
                },
                persona=persona
            )
        
        # Create patch info for tracking
        patch_info = {
            "id": str(uuid.uuid4()),
            "coordinate": coordinate,
            "operation": operation,
            "before": before_value,
            "after": value,
            "layer": self.layer_number,
            "reason": reason or f"Layer {self.layer_number} processing",
            "persona": persona or "system",
            "timestamp": datetime.now().isoformat()
        }
        
        # Log to audit system
        cert = make_patch_certificate(
            event="memory_patch",
            origin_layer=self.layer_number,
            data=patch_info,
            persona=persona
        )
        
        audit_logger.log(
            event_type="memory_patch",
            layer=self.layer_number,
            details=patch_info,
            persona=persona,
            certificate=cert
        )
        
        return patch_info
    
    def detect_fork(
        self,
        alternative_outputs: List[Dict[str, Any]],
        confidence_scores: List[float],
        threshold: float = 0.1
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if alternative reasoning paths (forks) should be created.
        
        Args:
            alternative_outputs: List of different possible outputs
            confidence_scores: Confidence scores for each alternative
            threshold: Minimum confidence difference to trigger fork
            
        Returns:
            Fork information if fork detected, None otherwise
        """
        if len(alternative_outputs) < 2:
            return None
            
        # Check if there are significantly different alternatives
        max_confidence = max(confidence_scores)
        alternatives_close = [
            (i, conf) for i, conf in enumerate(confidence_scores)
            if max_confidence - conf <= threshold
        ]
        
        if len(alternatives_close) > 1:
            # Fork detected - multiple viable alternatives
            fork_info = {
                "id": str(uuid.uuid4()),
                "layer": self.layer_number,
                "alternatives": [
                    {
                        "index": i,
                        "output": alternative_outputs[i],
                        "confidence": confidence_scores[i]
                    }
                    for i, conf in alternatives_close
                ],
                "reason": f"Multiple viable alternatives detected in Layer {self.layer_number}",
                "timestamp": datetime.now().isoformat()
            }
            
            return fork_info
            
        return None
    
    def check_safety_constraints(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        confidence: float
    ) -> Tuple[bool, List[str]]:
        """
        Check if this layer's output meets safety constraints.
        
        Returns:
            Tuple of (is_safe, list_of_violations)
        """
        violations = []
        
        # Basic safety checks
        if confidence < 0.5:
            violations.append("Extremely low confidence detected")
            
        if self.safety_critical and confidence < 0.99:
            violations.append("Safety-critical layer below required confidence")
            
        # Check for potential harmful content indicators
        if isinstance(output_data.get("answer"), str):
            answer = output_data["answer"].lower()
            harmful_indicators = [
                "cause harm", "dangerous", "illegal", "unethical"
            ]
            if any(indicator in answer for indicator in harmful_indicators):
                violations.append("Potential harmful content detected")
        
        return len(violations) == 0, violations
    
    def __str__(self):
        return f"Layer {self.layer_number}: {self.layer_name}"
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(layer={self.layer_number}, name='{self.layer_name}')>"


# Layer Registry for dynamic loading
class LayerRegistry:
    """Registry for managing and accessing simulation layers"""
    
    def __init__(self):
        self._layers: Dict[int, BaseLayer] = {}
        self._layer_classes: Dict[int, type] = {}
    
    def register_layer(self, layer_class: type, layer_number: int):
        """Register a layer class"""
        self._layer_classes[layer_number] = layer_class
        
    def get_layer(self, layer_number: int) -> Optional[BaseLayer]:
        """Get a layer instance by number"""
        if layer_number not in self._layers:
            if layer_number in self._layer_classes:
                self._layers[layer_number] = self._layer_classes[layer_number]()
            else:
                return None
        return self._layers[layer_number]
    
    def get_all_layers(self) -> List[BaseLayer]:
        """Get all registered layers in order"""
        layers = []
        for i in range(1, 11):  # Layers 1-10
            layer = self.get_layer(i)
            if layer:
                layers.append(layer)
        return layers
    
    def clear(self):
        """Clear all registered layers"""
        self._layers.clear()
        self._layer_classes.clear()

# Global registry instance
layer_registry = LayerRegistry()

def register_layer(layer_number: int):
    """Decorator to register a layer class"""
    def decorator(cls):
        layer_registry.register_layer(cls, layer_number)
        return cls
    return decorator