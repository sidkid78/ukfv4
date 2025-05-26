"""
Layer 1: Simulation Entry Layer (Enhanced with Gemini AI)
Handles query parsing, axis anchoring, and initial context setup with AI-powered analysis
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional
import asyncio

from .base import BaseLayer, LayerResult, register_layer
from core.memory import InMemoryKnowledgeGraph
from core.gemini_service import gemini_service, GeminiRequest, GeminiModel

@register_layer(1)
class Layer1SimulationEntry(BaseLayer):
    """
    Entry point for all simulations. Handles query parsing, 
    axis anchoring, and initial context establishment with AI-powered analysis.
    """
    
    def __init__(self):
        super().__init__()
        self.layer_number = 1
        self.layer_name = "Simulation Entry Layer"
        self.confidence_threshold = 0.95
        self.requires_memory = True
        self.requires_ai = True
        
    def process(
        self, 
        input_data: Dict[str, Any], 
        state: Dict[str, Any], 
        memory: InMemoryKnowledgeGraph,
        agents: Optional[List[Any]] = None
    ) -> LayerResult:
        """Process initial query and establish simulation context with AI analysis"""
        
        query = input_data.get("user_query", "")
        axes = input_data.get("axes", [0.0] * 13)
        context = input_data.get("context", {})
        session_id = state.get("session_id")
        
        # Use Gemini AI for advanced query analysis
        query_analysis = asyncio.run(self._ai_analyze_query(query, session_id))
        
        # Anchor axes based on AI analysis
        anchored_axes = self._anchor_axes_ai(axes, query_analysis)
        
        # Determine persona/role based on AI analysis
        persona = self._determine_persona_ai(query_analysis)
        
        # Check if we have existing knowledge for this query
        memory_cell = memory.get(anchored_axes, persona=persona)
        
        # Calculate confidence with AI insights
        confidence = self._calculate_entry_confidence_ai(query_analysis, memory_cell)
        
        # Determine if escalation is needed
        escalate = self.should_escalate(confidence) or query_analysis.get("requires_escalation", False)
        
        # Create enhanced output
        output = {
            "query": query,
            "normalized_query": query_analysis.get("normalized_query", query),
            "axes": anchored_axes,
            "persona": persona,
            "query_type": query_analysis.get("query_type", "general"),
            "complexity": query_analysis.get("complexity_score", 0.5),
            "intent": query_analysis.get("intent", "unknown"),
            "domain": query_analysis.get("domain", "general"),
            "safety_level": query_analysis.get("safety_level", "safe"),
            "memory_snapshot": memory_cell,
            "initial_context": context,
            "ai_insights": query_analysis.get("insights", [])
        }
        
        # Create detailed trace information
        trace = {
            "ai_analysis": query_analysis,
            "axes_anchored": anchored_axes != axes,
            "persona_assigned": persona,
            "memory_found": memory_cell is not None,
            "escalation_reason": query_analysis.get("escalation_reason"),
            "processing_mode": "ai_enhanced"
        }
        
        # Create patches if new insights should be stored
        patches = []
        if query_analysis.get("should_store_analysis", False):
            patches.append({
                "coordinate": anchored_axes,
                "value": {
                    "query_analysis": query_analysis,
                    "timestamp": datetime.now().isoformat(),
                    "layer": 1
                },
                "meta": {
                    "created_by": "layer_1_ai",
                    "persona": persona,
                    "confidence": confidence
                }
            })
        
        return LayerResult(
            output=output,
            confidence=confidence,
            escalate=escalate,
            trace=trace,
            patches=patches,
            metadata={
                "entry_point": True, 
                "query_length": len(query),
                "ai_enhanced": True,
                "ai_confidence": query_analysis.get("ai_confidence", 0.8)
            }
        )
    
    async def _ai_analyze_query(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Use Gemini AI for sophisticated query analysis"""
        
        analysis_prompt = f"""
        Analyze this user query for a multi-layered AI simulation system:
        
        Query: "{query}"
        
        Please provide a comprehensive analysis in JSON format with the following fields:
        
        1. normalized_query: A cleaned, standardized version of the query
        2. query_type: Category (question, analysis, prediction, risk_assessment, creative, technical, etc.)
        3. complexity_score: Numerical complexity (0.0-1.0)
        4. intent: What the user is trying to accomplish
        5. domain: Subject domain (science, business, creative, personal, etc.)
        6. safety_level: Assessment (safe, caution, high_risk)
        7. requires_escalation: Boolean - whether this needs advanced reasoning layers
        8. escalation_reason: Explanation if escalation is needed
        9. key_concepts: List of important concepts mentioned
        10. uncertainty_indicators: List of words/phrases indicating uncertainty
        11. insights: List of key insights about the query
        12. suggested_persona: Best AI persona for handling this query
        13. should_store_analysis: Whether this analysis should be stored for future reference
        14. ai_confidence: Your confidence in this analysis (0.0-1.0)
        
        Consider:
        - Complexity of reasoning required
        - Safety implications
        - Domain expertise needed
        - Ambiguity levels
        - Potential for multiple interpretations
        """
        
        try:
            request = GeminiRequest(
                prompt=analysis_prompt,
                model=GeminiModel.GEMINI_FLASH,
                temperature=0.3,  # Lower temperature for more consistent analysis
                system_prompt="You are an expert query analyzer for an advanced AI simulation system. Provide accurate, structured analysis in valid JSON format."
            )
            
            response = await gemini_service.generate_async(
                request, 
                session_id=session_id, 
                layer=1
            )
            
            # Try to parse JSON response
            try:
                import json
                analysis = json.loads(response.content)
                
                # Add Gemini response metadata
                analysis["gemini_confidence"] = response.confidence
                analysis["processing_time"] = response.processing_time
                
                return analysis
                
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return self._fallback_analysis(query, response.content)
                
        except Exception as e:
            # Fallback to rule-based analysis if AI fails
            return self._fallback_analysis(query, f"AI analysis failed: {str(e)}")
    
    def _fallback_analysis(self, query: str, error_info: str = "") -> Dict[str, Any]:
        """Fallback analysis using rule-based approach"""
        
        normalized = query.strip().lower()
        
        # Basic query type detection
        query_type = "general"
        if any(word in normalized for word in ["what", "how", "why", "when", "where"]):
            query_type = "question"
        elif any(word in normalized for word in ["analyze", "evaluate", "assess"]):
            query_type = "analysis"
        elif any(word in normalized for word in ["predict", "forecast", "future"]):
            query_type = "prediction"
        elif any(word in normalized for word in ["risk", "danger", "safety", "security"]):
            query_type = "risk_assessment"
        
        # Basic complexity calculation
        complexity = min(len(query) / 1000 + len(re.findall(r'\b(?:and|or|but|if|then|because)\b', normalized)) * 0.1, 1.0)
        
        return {
            "normalized_query": normalized,
            "query_type": query_type,
            "complexity_score": complexity,
            "intent": "unknown",
            "domain": "general",
            "safety_level": "safe",
            "requires_escalation": complexity > 0.6,
            "escalation_reason": "High complexity detected" if complexity > 0.6 else None,
            "key_concepts": query.split()[:5],  # First 5 words as concepts
            "uncertainty_indicators": [word for word in ["maybe", "perhaps", "possibly"] if word in normalized],
            "insights": ["Rule-based analysis used", error_info] if error_info else ["Rule-based analysis used"],
            "suggested_persona": "general_assistant",
            "should_store_analysis": False,
            "ai_confidence": 0.6,
            "fallback_used": True
        }
    
    def _anchor_axes_ai(self, axes: List[float], analysis: Dict[str, Any]) -> List[float]:
        """Anchor axes based on AI analysis results"""
        
        anchored = axes.copy()
        
        # Axis 0: AI-determined complexity
        anchored[0] = analysis.get("complexity_score", 0.5)
        
        # Axis 1: Query type encoding (more sophisticated)
        type_mapping = {
            "question": 0.1,
            "analysis": 0.3,
            "prediction": 0.5,
            "risk_assessment": 0.7,
            "creative": 0.9,
            "technical": 0.8,
            "general": 0.2
        }
        anchored[1] = type_mapping.get(analysis.get("query_type", "general"), 0.2)
        
        # Axis 2: Safety level
        safety_mapping = {
            "safe": 0.1,
            "caution": 0.5,
            "high_risk": 0.9
        }
        anchored[2] = safety_mapping.get(analysis.get("safety_level", "safe"), 0.1)
        
        # Axis 3: Domain complexity
        domain_complexity = {
            "general": 0.2,
            "science": 0.7,
            "technical": 0.8,
            "business": 0.6,
            "creative": 0.5,
            "personal": 0.3
        }
        anchored[3] = domain_complexity.get(analysis.get("domain", "general"), 0.2)
        
        # Axis 4: Uncertainty level
        uncertainty_count = len(analysis.get("uncertainty_indicators", []))
        anchored[4] = min(uncertainty_count * 0.3, 1.0)
        
        return anchored
    
    def _determine_persona_ai(self, analysis: Dict[str, Any]) -> str:
        """Determine optimal persona based on AI analysis"""
        
        suggested = analysis.get("suggested_persona", "general_assistant")
        
        # Map AI suggestions to available personas
        persona_mapping = {
            "general_assistant": "general_assistant",
            "safety_analyst": "safety_analyst",
            "domain_expert": "domain_expert",
            "technical_expert": "technical_specialist",
            "creative_assistant": "creative_reasoner",
            "research_analyst": "research_agent",
            "risk_assessor": "safety_analyst"
        }
        
        return persona_mapping.get(suggested, "general_assistant")
    
    def _calculate_entry_confidence_ai(
        self, 
        analysis: Dict[str, Any], 
        memory_cell: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate confidence incorporating AI analysis"""
        
        # Start with AI's confidence in its own analysis
        base_confidence = analysis.get("ai_confidence", 0.8)
        
        # Adjust based on complexity and safety
        complexity = analysis.get("complexity_score", 0.5)
        if complexity > 0.7:
            base_confidence *= 0.9
        
        safety_level = analysis.get("safety_level", "safe")
        if safety_level == "high_risk":
            base_confidence *= 0.8
        elif safety_level == "caution":
            base_confidence *= 0.9
        
        # Adjust based on available memory
        if memory_cell and not memory_cell.get("value", {}).get("generated_stub", False):
            base_confidence *= 1.1
        
        # Penalize if fallback analysis was used
        if analysis.get("fallback_used", False):
            base_confidence *= 0.8
        
        return min(1.0, max(0.1, base_confidence))
    
    def check_safety_constraints(
        self, 
        input_data: Dict[str, Any], 
        output_data: Dict[str, Any], 
        confidence: float
    ) -> tuple[bool, List[str]]:
        """Enhanced safety checking with AI insights"""
        
        violations = []
        
        # Check AI safety assessment
        safety_level = output_data.get("safety_level", "safe")
        if safety_level == "high_risk":
            violations.append("High-risk query detected by AI analysis")
        
        # Check confidence threshold
        if confidence < self.confidence_threshold:
            violations.append(f"Confidence {confidence:.3f} below threshold {self.confidence_threshold}")
        
        # Check for excessive complexity
        complexity = output_data.get("complexity", 0.0)
        if complexity > 0.9:
            violations.append("Query complexity exceeds safe processing limits")
        
        return len(violations) == 0, violations
