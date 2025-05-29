# backend/core/layers/layer_1.py
"""
Layer 1: Simulation Entry Layer
Handles query parsing, axis anchoring, and initial context setup
"""

import re
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from .base import BaseLayer, LayerResult, register_layer, logger
from core.memory import InMemoryKnowledgeGraph
from core.gemini_service import gemini_service, GeminiRequest, GeminiModel
import asyncio


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
        self.confidence_threshold = 0.75  # More realistic threshold
        self.requires_memory = True
        
    def process(
        self, 
        input_data: Dict[str, Any], 
        state: Dict[str, Any], 
        memory: InMemoryKnowledgeGraph,
        agents: Optional[List[Any]] = None
    ) -> LayerResult:
        """Process initial query and establish simulation context"""
        log_id = str(uuid.uuid4())[:8]
        logger.info(f"Layer 1 processing started | ID: {log_id} | Query: {input_data.get('user_query', '')[:50]}...")
        
        query = input_data.get("user_query", "")
        axes = input_data.get("axes", [0.0] * 13)
        context = input_data.get("context", {})
        
        # Parse query for intent and complexity
        logger.debug(f"Analyzing query | ID: {log_id}")
        query_analysis = self._analyze_query(query)
        logger.info(f"Query analysis complete | ID: {log_id} | Type: {query_analysis['type']} | Complexity: {query_analysis['complexity']:.2f}")
        
        # Anchor axes based on query type
        anchored_axes = self._anchor_axes(axes, query_analysis)
        logger.debug(f"Axes anchored | ID: {log_id} | Original: {axes} | Anchored: {anchored_axes}")
        
        # Determine persona/role based on query
        persona = self._determine_initial_persona(query_analysis)
        logger.info(f"Persona assigned | ID: {log_id} | Persona: {persona}")
        
        # Check if we have existing knowledge for this query
        memory_cell = memory.get(anchored_axes, persona=persona)
        logger.debug(f"Memory lookup | ID: {log_id} | Found: {memory_cell is not None}")
        
        # Calculate confidence based on query clarity and existing knowledge
        confidence = self._calculate_entry_confidence(query_analysis, memory_cell)
        logger.info(f"Confidence calculated | ID: {log_id} | Value: {confidence:.2f}")
        
        # Determine if escalation is needed based on confidence and severe complexity
        escalate = self.should_escalate(confidence) or (query_analysis["complexity"] > 0.8 and confidence < 0.8)
        if escalate:
            reason = "Complex query" if query_analysis["complexity"] > 0.8 else "Low confidence"
            logger.warning(f"Escalation triggered | ID: {log_id} | Reason: {reason}")
        
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
        
        logger.info(f"Layer 1 processing complete | ID: {log_id} | Confidence: {confidence:.2f} | Escalate: {escalate}")
        return LayerResult(
            output=output,
            confidence=confidence,
            escalate=escalate,
            trace=trace,
            metadata={
                "entry_point": True,
                "query_length": len(query),
                "log_id": log_id
            }
        )
    
    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query using AI for intent, complexity, and normalization"""
        logger.debug(f"AI-powered query analysis for: {query[:50]}...")
        
        # Use AI to analyze the query
        ai_request = GeminiRequest(
            prompt=f"Analyze this user query comprehensively: '{query}'",
            system_prompt="""You are an expert query analyzer. Analyze the user's query and provide structured analysis.
            
            Determine:
            1. Query type (question, analysis, prediction, risk_assessment, general)
            2. Complexity score (0.0-1.0 based on conceptual difficulty, length, multi-part nature)
            3. Ambiguity indicators (unclear terms, multiple interpretations)
            4. Question words and key terms
            5. Normalized/cleaned version
            
            Respond in this EXACT format:
            TYPE: [question|analysis|prediction|risk_assessment|general]
            COMPLEXITY: [0.0-1.0]
            NORMALIZED: [cleaned query]
            AMBIGUITY: [true|false]
            WORD_COUNT: [number]
            QUESTION_WORDS: [number]
            REASONING: [brief explanation]""",
            model=GeminiModel.GEMINI_FLASH,
            temperature=0.2  # Low temperature for consistent analysis
        )
        
        try:
            response = asyncio.run(gemini_service.generate_async(ai_request, layer=1))
            content = response.content
            
            # Parse the structured response
            analysis = self._parse_ai_analysis(content, query)
            
            logger.info(f"AI query analysis complete - Type: {analysis['type']}, Complexity: {analysis['complexity']:.2f}")
            return analysis
            
        except Exception as e:
            logger.error(f"AI query analysis failed: {str(e)}, falling back to rule-based")
            # Fallback to original rule-based analysis
            return self._fallback_query_analysis(query)
    
    def _parse_ai_analysis(self, content: str, original_query: str) -> Dict[str, Any]:
        """Parse structured AI analysis response"""
        lines = content.strip().split('\n')
        analysis = {
            "original": original_query,
            "normalized": original_query.strip().lower(),
            "type": "general",
            "complexity": 0.5,
            "ambiguity_detected": False,
            "word_count": len(original_query.split()),
            "question_words": 0
        }
        
        # Parse each line of the AI response
        for line in lines:
            line = line.strip()
            if line.startswith("TYPE:"):
                type_val = line.replace("TYPE:", "").strip().lower()
                if type_val in ["question", "analysis", "prediction", "risk_assessment", "general"]:
                    analysis["type"] = type_val
            
            elif line.startswith("COMPLEXITY:"):
                try:
                    complexity = float(line.replace("COMPLEXITY:", "").strip())
                    analysis["complexity"] = max(0.0, min(1.0, complexity))
                except ValueError:
                    pass
            
            elif line.startswith("NORMALIZED:"):
                normalized = line.replace("NORMALIZED:", "").strip()
                if normalized and len(normalized) > 2:
                    analysis["normalized"] = normalized
            
            elif line.startswith("AMBIGUITY:"):
                ambiguity = line.replace("AMBIGUITY:", "").strip().lower()
                analysis["ambiguity_detected"] = ambiguity == "true"
            
            elif line.startswith("WORD_COUNT:"):
                try:
                    word_count = int(line.replace("WORD_COUNT:", "").strip())
                    analysis["word_count"] = word_count
                except ValueError:
                    pass
            
            elif line.startswith("QUESTION_WORDS:"):
                try:
                    q_words = int(line.replace("QUESTION_WORDS:", "").strip())
                    analysis["question_words"] = q_words
                except ValueError:
                    pass
        
        return analysis
    
    def _fallback_query_analysis(self, query: str) -> Dict[str, Any]:
        """Fallback rule-based analysis when AI fails"""
        normalized = query.strip().lower()
        
        # Determine query type
        query_type = "general"
        type_markers = {
            "question": ["what", "how", "why", "when", "where"],
            "analysis": ["analyze", "evaluate", "assess"],
            "prediction": ["predict", "forecast", "future"],
            "risk_assessment": ["risk", "danger", "safety", "security"]
        }
        
        for qtype, markers in type_markers.items():
            if any(word in normalized for word in markers):
                query_type = qtype
                break
        
        # Calculate complexity
        complexity = 0.0
        complexity += min(len(query) / 1000, 0.3)
        complexity += len(re.findall(r'\b(?:and|or|but|if|then|because)\b', normalized)) * 0.1
        complexity += len(re.findall(r'\b(?:should|would|could|might|may)\b', normalized)) * 0.1
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
        type_mapping = {
            "question": 0.2,
            "analysis": 0.4,
            "prediction": 0.6,
            "risk_assessment": 0.8,
            "general": 0.1
        }
        
        anchored[0] = query_analysis["complexity"]
        anchored[1] = type_mapping.get(query_analysis["type"], 0.1)
        anchored[2] = 0.8 if query_analysis["ambiguity_detected"] else 0.2
        
        return anchored
    
    def _determine_initial_persona(self, query_analysis: Dict[str, Any]) -> str:
        """Determine initial persona using AI-enhanced logic"""
        query = query_analysis["original"]
        query_type = query_analysis["type"]
        complexity = query_analysis["complexity"]
        ambiguity = query_analysis["ambiguity_detected"]
        
        # For complex or ambiguous queries, use AI to determine best persona
        if complexity > 0.6 or ambiguity:
            try:
                ai_request = GeminiRequest(
                    prompt=f"What type of expert would be best suited to handle this query: '{query}'",
                    system_prompt="""You are a persona assignment expert. Given a user query, determine the most appropriate expert persona.
                    
                    Available personas:
                    - safety_analyst: For safety, risk, security concerns
                    - domain_expert: For technical, specialized knowledge
                    - forecaster: For predictions, future trends
                    - complex_reasoner: For multi-faceted, complex problems
                    - general_assistant: For simple, straightforward queries
                    - creative_thinker: For innovative, creative challenges
                    
                    Respond with ONLY the persona name, no explanation.""",
                    model=GeminiModel.GEMINI_FLASH,
                    temperature=0.1
                )
                
                response = asyncio.run(gemini_service.generate_async(ai_request, layer=1))
                ai_persona = response.content.strip().lower()
                
                # Validate AI response and use if valid
                valid_personas = ["safety_analyst", "domain_expert", "forecaster", "complex_reasoner", "general_assistant", "creative_thinker"]
                if ai_persona in valid_personas:
                    logger.info(f"AI-selected persona: {ai_persona}")
                    return ai_persona
                    
            except Exception as e:
                logger.warning(f"AI persona selection failed: {str(e)}, using rule-based")
        
        # Fallback to rule-based persona selection
        persona_map = {
            "risk_assessment": "safety_analyst",
            "analysis": "domain_expert",
            "prediction": "forecaster"
        }
        
        return persona_map.get(query_type, 
                             "complex_reasoner" if complexity > 0.7 
                             else "general_assistant")
    
    def _calculate_entry_confidence(
        self, 
        query_analysis: Dict[str, Any], 
        memory_cell: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate confidence for entry layer processing"""
        base_confidence = 0.9
        
        if query_analysis["complexity"] > 0.5:
            base_confidence *= 0.9
        if query_analysis["ambiguity_detected"]:
            base_confidence *= 0.85
        if memory_cell and not memory_cell.get("value", {}).get("generated_stub", False):
            base_confidence *= 1.05
        
        return min(1.0, max(0.1, base_confidence))