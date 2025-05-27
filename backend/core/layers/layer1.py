# backend/core/layers/layer_1.py
"""
Layer 1: Simulation Entry Layer
Handles query parsing, axis anchoring, and initial context setup
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from .base import BaseLayer, LayerResult, register_layer
from core.memory import InMemoryKnowledgeGraph


@register_layer(1)
class Layer1SimulationEntry(BaseLayer):
    """
    Entry point for all simulations. Handles query parsing, 
    axis anchoring, and initial context establishment.
    """
    
    def __init__(self):
        super().__init__()
        self.layer_number = 1
        self.layer_name = "Simulation Entry Layer"
        self.confidence_threshold = 0.95
        self.requires_memory = True
        
    def process(
        self, 
        input_data: Dict[str, Any], 
        state: Dict[str, Any], 
        memory: InMemoryKnowledgeGraph,
        agents: Optional[List[Any]] = None
    ) -> LayerResult:
        """Process initial query and establish simulation context"""
        
        query = input_data.get("user_query", "")
        axes = input_data.get("axes", [0.0] * 13)
        context = input_data.get("context", {})
        
        # Parse query for intent and complexity
        query_analysis = self._analyze_query(query)
        
        # Anchor axes based on query type
        anchored_axes = self._anchor_axes(axes, query_analysis)
        
        # Determine persona/role based on query
        persona = self._determine_initial_persona(query_analysis)
        
        # Check if we have existing knowledge for this query
        memory_cell = memory.get(anchored_axes, persona=persona)
        
        # Calculate confidence based on query clarity and existing knowledge
        confidence = self._calculate_entry_confidence(query_analysis, memory_cell)
        
        # Determine if escalation is needed
        escalate = self.should_escalate(confidence) or query_analysis["complexity"] > 0.7
        
        # Create output
        output = {
            "query": query,
            "normalized_query": query_analysis["normalized"],
            "axes": anchored_axes,
            "persona": persona,
            "query_type": query_analysis["type"],
            "complexity": query_analysis["complexity"],
            "memory_snapshot": memory_cell,
            "initial_context": context
        }
        
        # Create trace information
        trace = {
            "query_analysis": query_analysis,
            "axes_anchored": anchored_axes != axes,
            "persona_assigned": persona,
            "memory_found": memory_cell is not None,
            "escalation_reason": "Complex query detected" if escalate else None
        }
        
        return LayerResult(
            output=output,
            confidence=confidence,
            escalate=escalate,
            trace=trace,
            metadata={"entry_point": True, "query_length": len(query)}
        )
    
    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query for type, complexity, and normalization"""
        
        normalized = query.strip().lower()
        
        # Determine query type
        query_type = "general"
        if any(word in normalized for word in ["what", "how", "why", "when", "where"]):
            query_type = "question"
        elif any(word in normalized for word in ["analyze", "evaluate", "assess"]):
            query_type = "analysis"
        elif any(word in normalized for word in ["predict", "forecast", "future"]):
            query_type = "prediction"
        elif any(word in normalized for word in ["risk", "danger", "safety", "security"]):
            query_type = "risk_assessment"
        
        # Calculate complexity
        complexity = 0.0
        complexity += min(len(query) / 1000, 0.3)  # Length factor
        complexity += len(re.findall(r'\b(?:and|or|but|if|then|because)\b', normalized)) * 0.1  # Logical connectors
        complexity += len(re.findall(r'\b(?:should|would|could|might|may)\b', normalized)) * 0.1  # Uncertainty markers
        complexity = min(complexity, 1.0)
        
        # Detect ambiguity indicators
        ambiguity_markers = ["maybe", "perhaps", "possibly", "uncertain", "unclear"]
        ambiguity_detected = any(marker in normalized for marker in ambiguity_markers)
        
        return {
            "original": query,
            "normalized": normalized,
            "type": query_type,
            "complexity": complexity,
            "ambiguity_detected": ambiguity_detected,
            "word_count": len(query.split()),
            "question_words": len(re.findall(r'\b(?:what|how|why|when|where|who)\b', normalized))
        }
    
    def _anchor_axes(self, axes: List[float], query_analysis: Dict[str, Any]) -> List[float]:
        """Anchor axes based on query characteristics"""
        
        anchored = axes.copy()
        
        # Axis 0: Query complexity
        anchored[0] = query_analysis["complexity"]
        
        # Axis 1: Query type encoding
        type_mapping = {
            "question": 0.2,
            "analysis": 0.4,
            "prediction": 0.6,
            "risk_assessment": 0.8,
            "general": 0.1
        }
        anchored[1] = type_mapping.get(query_analysis["type"], 0.1)
        
        # Axis 2: Ambiguity level
        anchored[2] = 0.8 if query_analysis["ambiguity_detected"] else 0.2
        
        return anchored
    
    def _determine_initial_persona(self, query_analysis: Dict[str, Any]) -> str:
        """Determine initial persona based on query type"""
        
        if query_analysis["type"] == "risk_assessment":
            return "safety_analyst"
        elif query_analysis["type"] == "analysis":
            return "domain_expert"
        elif query_analysis["type"] == "prediction":
            return "forecaster"
        elif query_analysis["complexity"] > 0.7:
            return "complex_reasoner"
        else:
            return "general_assistant"
    
    def _calculate_entry_confidence(
        self, 
        query_analysis: Dict[str, Any], 
        memory_cell: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate confidence for entry layer processing"""
        
        base_confidence = 0.9
        
        # Reduce confidence for complex or ambiguous queries
        if query_analysis["complexity"] > 0.5:
            base_confidence *= 0.9
        
        if query_analysis["ambiguity_detected"]:
            base_confidence *= 0.85
        
        # Increase confidence if we have relevant memory
        if memory_cell and not memory_cell.get("value", {}).get("generated_stub", False):
            base_confidence *= 1.05
        
        return min(1.0, max(0.1, base_confidence))