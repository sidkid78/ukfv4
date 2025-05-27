"""
Layer 3: Research Agents Layer
Handles multi-agent reasoning, research coordination, and consensus building
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from .base import BaseLayer, LayerResult, register_layer
from core.memory import InMemoryKnowledgeGraph


@register_layer(3)
class Layer3ResearchAgents(BaseLayer):
    """
    Multi-agent research layer. Spawns and coordinates research agents
    for complex reasoning, hypothesis generation, and consensus building.
    """
    
    def __init__(self):
        super().__init__()
        self.layer_number = 3
        self.layer_name = "Research Agents Layer"
        self.confidence_threshold = 0.995
        self.requires_agents = True
        self.requires_memory = True
        
    def process(
        self, 
        input_data: Dict[str, Any], 
        state: Dict[str, Any], 
        memory: InMemoryKnowledgeGraph,
        agents: Optional[List[Any]] = None
    ) -> LayerResult:
        """Process multi-agent research and reasoning"""
        
        query = input_data.get("normalized_query", input_data.get("query", ""))
        complexity = input_data.get("complexity", 0.5)
        knowledge_available = input_data.get("knowledge_available", False)
        
        # Determine research strategy based on available knowledge and complexity
        research_strategy = self._determine_research_strategy(
            complexity, knowledge_available, input_data
        )
        
        # Spawn appropriate research agents
        research_agents = self._spawn_research_agents(research_strategy, query, state)
        
        # Coordinate agent research
        agent_results = self._coordinate_agent_research(
            research_agents, input_data, memory
        )
        
        # Analyze agent consensus and conflicts
        consensus_analysis = self._analyze_agent_consensus(agent_results)
        
        # Detect and handle forks if agents significantly disagree
        forks = self._detect_reasoning_forks(agent_results, consensus_analysis)
        
        # Generate final research output
        research_output = self._synthesize_agent_results(
            agent_results, consensus_analysis, input_data
        )
        
        # Calculate confidence based on agent agreement and result quality
        confidence = self._calculate_research_confidence(
            agent_results, consensus_analysis, research_output
        )
        
        # Determine escalation need
        escalate = (
            self.should_escalate(confidence) or 
            consensus_analysis["major_disagreement"] or
            research_output.get("requires_expert_review", False)
        )
        
        output = {
            **input_data,
            "research_conducted": True,
            "research_strategy": research_strategy,
            "agent_results": agent_results,
            "consensus_analysis": consensus_analysis,
            "research_answer": research_output.get("answer"),
            "research_confidence": research_output.get("confidence"),
            "alternative_hypotheses": research_output.get("alternatives", []),
            "evidence_quality": research_output.get("evidence_quality", "medium")
        }
        
        trace = {
            "research_strategy": research_strategy,
            "agents_spawned": len(research_agents),
            "consensus_reached": consensus_analysis["consensus_strength"] > 0.7,
            "major_disagreements": consensus_analysis["major_disagreement"],
            "forks_detected": len(forks),
            "persona_reasonings": {
                agent["persona"]: agent["reasoning"]
                for agent in agent_results
                if "reasoning" in agent
            }
        }
        
        return LayerResult(
            output=output,
            confidence=confidence,
            escalate=escalate,
            trace=trace,
            forks=forks,
            agents_spawned=[agent["id"] for agent in research_agents],
            metadata={"research_layer": True, "agent_count": len(research_agents)}
        )
    
    def _determine_research_strategy(
        self, 
        complexity: float, 
        knowledge_available: bool, 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine the research strategy based on query characteristics"""
        
        query_type = input_data.get("query_type", "general")
        
        strategy = {
            "approach": "collaborative",
            "agent_count": 3,
            "research_depth": "medium",
            "consensus_requirement": 0.7,
            "specialization_needed": False
        }
        
        # Adjust based on complexity
        if complexity > 0.7:
            strategy["agent_count"] = 5
            strategy["research_depth"] = "deep"
            strategy["consensus_requirement"] = 0.8
        elif complexity < 0.3:
            strategy["agent_count"] = 2
            strategy["research_depth"] = "shallow"
        
        # Adjust based on query type
        if query_type == "risk_assessment":
            strategy["specialization_needed"] = True
            strategy["agent_count"] += 1  # Add safety specialist
            strategy["consensus_requirement"] = 0.9
        elif query_type == "analysis":
            strategy["approach"] = "multi_perspective"
            strategy["agent_count"] = 4
        
        # Adjust based on knowledge availability
        if not knowledge_available:
            strategy["research_depth"] = "deep"
            strategy["agent_count"] += 1
        
        return strategy
    
    def _spawn_research_agents(
        self, 
        strategy: Dict[str, Any], 
        query: str, 
        state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Spawn research agents based on strategy"""
        
        agents = []
        agent_count = strategy["agent_count"]
        
        # Define agent personas based on research needs
        base_personas = [
            {"persona": "domain_expert", "role": "Expert analysis and fact-checking"},
            {"persona": "critical_thinker", "role": "Challenge assumptions and find flaws"},
            {"persona": "creative_reasoner", "role": "Generate alternative perspectives"},
            {"persona": "synthesizer", "role": "Combine insights and build consensus"},
            {"persona": "safety_analyst", "role": "Identify risks and safety concerns"}
        ]
        
        # Select appropriate personas
        selected_personas = base_personas[:agent_count]
        
        # Add specialized agents if needed
        if strategy.get("specialization_needed", False):
            selected_personas.append({
                "persona": "risk_specialist", 
                "role": "Deep risk analysis and mitigation"
            })
        
        # Create agent instances
        for i, persona_info in enumerate(selected_personas):
            agent = {
                "id": f"research_agent_{uuid.uuid4().hex[:8]}",
                "persona": persona_info["persona"],
                "role": persona_info["role"],
                "query_focus": query,
                "strategy": strategy,
                "spawned_at": datetime.now().isoformat(),
                "active": True
            }
            agents.append(agent)
        
        return agents
    
    def _coordinate_agent_research(
        self, 
        agents: List[Dict[str, Any]], 
        input_data: Dict[str, Any], 
        memory: InMemoryKnowledgeGraph
    ) -> List[Dict[str, Any]]:
        """Coordinate research across all agents"""
        
        results = []
        
        for agent in agents:
            # Simulate agent research process
            agent_result = self._simulate_agent_research(agent, input_data, memory)
            results.append(agent_result)
        
        return results
    
    def _simulate_agent_research(
        self, 
        agent: Dict[str, Any], 
        input_data: Dict[str, Any], 
        memory: InMemoryKnowledgeGraph
    ) -> Dict[str, Any]:
        """Simulate individual agent research process"""
        
        persona = agent["persona"]
        query = input_data.get("normalized_query", "")
        
        # Persona-specific research approach
        if persona == "domain_expert":
            answer, confidence, reasoning = self._expert_analysis(query, input_data, memory)
        elif persona == "critical_thinker":
            answer, confidence, reasoning = self._critical_analysis(query, input_data, memory)
        elif persona == "creative_reasoner":
            answer, confidence, reasoning = self._creative_analysis(query, input_data, memory)
        elif persona == "synthesizer":
            answer, confidence, reasoning = self._synthesis_analysis(query, input_data, memory)
        elif persona in ["safety_analyst", "risk_specialist"]:
            answer, confidence, reasoning = self._safety_analysis(query, input_data, memory)
        else:
            answer, confidence, reasoning = self._general_analysis(query, input_data, memory)
        
        return {
            "agent_id": agent["id"],
            "persona": persona,
            "answer": answer,
            "confidence": confidence,
            "reasoning": reasoning,
            "research_time": 0.5,  # Simulated processing time
            "evidence_strength": "medium",
            "alternative_considered": True
        }
    
    def _expert_analysis(self, query: str, input_data: Dict[str, Any], memory) -> tuple:
        """Domain expert analysis approach"""
        knowledge_available = input_data.get("knowledge_available", False)
        
        if knowledge_available and input_data.get("memory_answer"):
            answer = f"Expert analysis confirms: {input_data['memory_answer']}"
            confidence = 0.92
            reasoning = "Based on domain expertise and available knowledge base"
        else:
            answer = f"Expert assessment of '{query}' requires additional research and validation"
            confidence = 0.75
            reasoning = "Limited domain knowledge available, requires deeper investigation"
        
        return answer, confidence, reasoning
    
    def _critical_analysis(self, query: str, input_data: Dict[str, Any], memory) -> tuple:
        """Critical thinking analysis approach"""
        answer = f"Critical analysis of '{query}' reveals multiple assumptions that need validation"
        confidence = 0.70
        reasoning = "Identified potential biases and unvalidated assumptions in the query premise"
        return answer, confidence, reasoning
    
    def _creative_analysis(self, query: str, input_data: Dict[str, Any], memory) -> tuple:
        """Creative reasoning analysis approach"""
        answer = f"Alternative perspective on '{query}': Consider unconventional approaches and paradigm shifts"
        confidence = 0.68
        reasoning = "Generated alternative viewpoints and creative solutions not typically considered"
        return answer, confidence, reasoning
    
    def _synthesis_analysis(self, query: str, input_data: Dict[str, Any], memory) -> tuple:
        """Synthesis analysis approach"""
        answer = f"Synthesized understanding of '{query}' integrating multiple perspectives and evidence sources"
        confidence = 0.85
        reasoning = "Combined insights from available evidence and multiple analytical approaches"
        return answer, confidence, reasoning
    
    def _safety_analysis(self, query: str, input_data: Dict[str, Any], memory) -> tuple:
        """Safety and risk analysis approach"""
        answer = f"Safety analysis of '{query}' identifies potential risks and mitigation strategies"
        confidence = 0.88
        reasoning = "Comprehensive risk assessment with focus on harm prevention and safety protocols"
        return answer, confidence, reasoning
    
    def _general_analysis(self, query: str, input_data: Dict[str, Any], memory) -> tuple:
        """General analysis approach"""
        answer = f"General analysis of '{query}' provides balanced perspective"
        confidence = 0.80
        reasoning = "Balanced analysis considering multiple factors and perspectives"
        return answer, confidence, reasoning
    
    def _analyze_agent_consensus(self, agent_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze consensus and disagreement among agents"""
        
        if not agent_results:
            return {"consensus_strength": 0.0, "major_disagreement": True}
        
        confidences = [r["confidence"] for r in agent_results]
        avg_confidence = sum(confidences) / len(confidences)
        confidence_variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)
        
        # Simple consensus analysis (would be more sophisticated in production)
        consensus_strength = max(0.0, 1.0 - confidence_variance * 2)
        major_disagreement = confidence_variance > 0.15
        
        # Find most confident agent
        best_agent_idx = confidences.index(max(confidences))
        best_agent = agent_results[best_agent_idx]
        
        return {
            "consensus_strength": consensus_strength,
            "major_disagreement": major_disagreement,
            "avg_confidence": avg_confidence,
            "confidence_variance": confidence_variance,
            "best_agent": best_agent,
            "agreement_level": "high" if consensus_strength > 0.8 else "medium" if consensus_strength > 0.5 else "low"
        }
    
    def _detect_reasoning_forks(
        self, 
        agent_results: List[Dict[str, Any]], 
        consensus_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect significant disagreements that warrant forking"""
        
        forks = []
        
        if consensus_analysis["major_disagreement"]:
            # Group agents by similar confidence levels
            high_conf_agents = [r for r in agent_results if r["confidence"] > 0.8]
            low_conf_agents = [r for r in agent_results if r["confidence"] < 0.6]
            
            if len(high_conf_agents) > 0 and len(low_conf_agents) > 0:
                fork_info = {
                    "id": str(uuid.uuid4()),
                    "layer": self.layer_number,
                    "type": "confidence_disagreement",
                    "high_confidence_path": {
                        "agents": [a["agent_id"] for a in high_conf_agents],
                        "consensus": high_conf_agents[0]["answer"],
                        "confidence": max(a["confidence"] for a in high_conf_agents)
                    },
                    "low_confidence_path": {
                        "agents": [a["agent_id"] for a in low_conf_agents],
                        "concerns": [a["reasoning"] for a in low_conf_agents],
                        "avg_confidence": sum(a["confidence"] for a in low_conf_agents) / len(low_conf_agents)
                    },
                    "reason": "Significant disagreement in agent confidence levels",
                    "requires_resolution": True
                }
                forks.append(fork_info)
        
        return forks
    
    def _synthesize_agent_results(
        self, 
        agent_results: List[Dict[str, Any]], 
        consensus_analysis: Dict[str, Any], 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize final research output from agent results"""
        
        if not agent_results:
            return {
                "answer": "Unable to conduct research - no agents available",
                "confidence": 0.1,
                "requires_expert_review": True
            }
        
        best_agent = consensus_analysis["best_agent"]
        
        # Create synthesized answer
        if consensus_analysis["agreement_level"] == "high":
            answer = best_agent["answer"]
            confidence = min(0.99, best_agent["confidence"] * 1.1)  # Boost for consensus
            requires_review = False
        else:
            answer = f"Research indicates: {best_agent['answer']} (Note: Agents showed disagreement)"
            confidence = best_agent["confidence"] * 0.9  # Reduce for disagreement
            requires_review = True
        
        # Collect alternative hypotheses
        alternatives = []
        for agent in agent_results:
            if agent["agent_id"] != best_agent["agent_id"] and agent["confidence"] > 0.6:
                alternatives.append({
                    "hypothesis": agent["answer"],
                    "confidence": agent["confidence"],
                    "persona": agent["persona"]
                })
        
        return {
            "answer": answer,
            "confidence": confidence,
            "alternatives": alternatives,
            "evidence_quality": "high" if consensus_analysis["agreement_level"] == "high" else "medium",
            "requires_expert_review": requires_review
        }
    
    def _calculate_research_confidence(
        self, 
        agent_results: List[Dict[str, Any]], 
        consensus_analysis: Dict[str, Any], 
        research_output: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence for research layer"""
        
        if not agent_results:
            return 0.1
        
        base_confidence = consensus_analysis["avg_confidence"]
        
        # Boost for high consensus
        if consensus_analysis["agreement_level"] == "high":
            base_confidence *= 1.1
        elif consensus_analysis["agreement_level"] == "low":
            base_confidence *= 0.8
        
        # Boost for multiple high-confidence agents
        high_conf_count = sum(1 for r in agent_results if r["confidence"] > 0.8)
        if high_conf_count >= 3:
            base_confidence *= 1.05
        
        return min(1.0, max(0.1, base_confidence))
