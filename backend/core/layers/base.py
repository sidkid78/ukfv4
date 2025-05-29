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
import json
from pathlib import Path

from models.simulation import ConfidenceScore, TraceStep, EventType, SimulationLayer
from core.memory import InMemoryKnowledgeGraph
from core.audit import audit_logger, make_patch_certificate
from core.compliance import compliance_engine

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configure file handler for layer logs
log_file = Path(__file__).parent.parent.parent / 'logs' / 'simulation_layers.log'
log_file.parent.mkdir(exist_ok=True, parents=True)
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

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

        logger.debug(
            "Initialized LayerResult for layer %d: Confidence=%.3f, Escalate=%s",
            metadata.get('layer_number', 0) if metadata else 0,
            confidence,
            escalate
        )

class BaseLayer(ABC):
    """
    Abstract base class for all simulation layers.
    Provides common functionality and enforces layer interface.
    """
    
    def __init__(self):
        self.layer_number: SimulationLayer = 1
        self.layer_name: str = "BaseLayer"
        self.confidence_threshold: float = 0.85  # More realistic default threshold
        self.entropy_threshold: float = 0.1
        self.max_processing_time: float = 30.0  # seconds
        self.requires_agents: bool = False
        self.requires_memory: bool = True
        self.safety_critical: bool = False
        
        logger.info("Initialized %s (Layer %d)", self.__class__.__name__, self.layer_number)
    
    @abstractmethod
    def process(
        self,
        input_data: Dict[str, Any],
        state: Dict[str, Any],
        memory: InMemoryKnowledgeGraph,
        agents: Optional[List[Any]] = None
    ) -> LayerResult:
        pass
    
    def should_escalate(
        self, 
        confidence: float, 
        entropy: Optional[float] = None,
        context: Dict[str, Any] = None
    ) -> bool:
        escalation_reason = None
        if confidence < self.confidence_threshold:
            escalation_reason = f"Low confidence ({confidence:.3f} < {self.confidence_threshold:.3f})"
        elif entropy and entropy > self.entropy_threshold:
            escalation_reason = f"High entropy ({entropy:.3f} > {self.entropy_threshold:.3f})"
        
        if escalation_reason:
            logger.warning(
                "Escalation triggered in layer %d: %s",
                self.layer_number,
                escalation_reason
            )
            return True
        return False
    
    def calculate_confidence(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> float:
        base_confidence = 0.9
        
        if not output_data or not input_data:
            base_confidence *= 0.5
            logger.debug("Reduced confidence in layer %d due to missing data", self.layer_number)
            
        if context:
            if context.get("ambiguity_detected", False):
                base_confidence *= 0.8
                logger.debug("Ambiguity penalty applied in layer %d", self.layer_number)
            if context.get("conflict_detected", False):
                base_confidence *= 0.7
                logger.debug("Conflict penalty applied in layer %d", self.layer_number)
                
        final_confidence = min(1.0, max(0.0, base_confidence))
        logger.debug(
            "Calculated confidence for layer %d: %.3f",
            self.layer_number,
            final_confidence
        )
        return final_confidence
    
    def calculate_entropy(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> float:
        base_entropy = 0.05
        
        if isinstance(input_data.get("query"), str):
            query_length = len(input_data["query"])
            if query_length > 500:
                base_entropy += 0.02
                logger.debug(
                    "Increased entropy in layer %d for long query (%d chars)",
                    self.layer_number,
                    query_length
                )
                
        final_entropy = min(1.0, max(0.0, base_entropy))
        logger.debug(
            "Calculated entropy for layer %d: %.3f",
            self.layer_number,
            final_entropy
        )
        return final_entropy
    
    def create_trace_step(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        event_type: EventType,
        confidence: float,
        message: str,
        metadata: Dict[str, Any] = None
    ) -> TraceStep:
        logger.info(
            "Creating trace step in layer %d: %s",
            self.layer_number,
            message
        )
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
                delta=0.0,
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
        current_cell = memory.get(coordinate, persona=persona)
        before_value = current_cell.get("value") if current_cell else None
        
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
        
        logger.info(
            "Memory patch applied in layer %d: %s",
            self.layer_number,
            json.dumps(patch_info, default=str)
        )
        
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
        if len(alternative_outputs) < 2:
            return None
            
        max_confidence = max(confidence_scores)
        alternatives_close = [
            (i, conf) for i, conf in enumerate(confidence_scores)
            if max_confidence - conf <= threshold
        ]
        
        if len(alternatives_close) > 1:
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
            
            logger.warning(
                "Fork detected in layer %d with %d alternatives",
                self.layer_number,
                len(alternatives_close)
            )
            return fork_info
            
        return None
    
    def check_safety_constraints(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        confidence: float
    ) -> Tuple[bool, List[str]]:
        violations = []
        
        if confidence < 0.5:
            violations.append("Extremely low confidence detected")
            
        if self.safety_critical and confidence < 0.99:
            violations.append("Safety-critical layer below required confidence")
            
        if isinstance(output_data.get("answer"), str):
            answer = output_data["answer"].lower()
            harmful_indicators = [
                "cause harm", "dangerous", "illegal", "unethical"
            ]
            if any(indicator in answer for indicator in harmful_indicators):
                violations.append("Potential harmful content detected")
        
        if violations:
            logger.error(
                "Safety constraints violated in layer %d: %s",
                self.layer_number,
                violations
            )
        
        return len(violations) == 0, violations
    
    def __str__(self):
        return f"Layer {self.layer_number}: {self.layer_name}"
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(layer={self.layer_number}, name='{self.layer_name}')>"


class LayerRegistry:
    """Registry for managing and accessing simulation layers"""
    
    def __init__(self):
        self._layers: Dict[int, BaseLayer] = {}
        self._layer_classes: Dict[int, type] = {}
        logger.info("LayerRegistry initialized")
    
    def register_layer(self, layer_class: type, layer_number: int):
        logger.debug(
            "Registering layer %d: %s",
            layer_number,
            layer_class.__name__
        )
        self._layer_classes[layer_number] = layer_class
        
    def get_layer(self, layer_number: int) -> Optional[BaseLayer]:
        if layer_number not in self._layers:
            if layer_number in self._layer_classes:
                logger.debug(
                    "Instantiating layer %d: %s",
                    layer_number,
                    self._layer_classes[layer_number].__name__
                )
                self._layers[layer_number] = self._layer_classes[layer_number]()
            else:
                logger.warning("Requested unregistered layer %d", layer_number)
                return None
        return self._layers[layer_number]
    
    def get_all_layers(self) -> List[BaseLayer]:
        layers = []
        for i in range(1, 11):
            layer = self.get_layer(i)
            if layer:
                layers.append(layer)
            else:
                logger.error("Missing registered layer %d", i)
        return layers
    
    def clear(self):
        logger.info("Clearing all registered layers")
        self._layers.clear()
        self._layer_classes.clear()

layer_registry = LayerRegistry()

def register_layer(layer_number: int):
    def decorator(cls):
        logger.info(
            "Registering layer %d via decorator: %s",
            layer_number,
            cls.__name__
        )
        layer_registry.register_layer(cls, layer_number)
        return cls
    return decorator