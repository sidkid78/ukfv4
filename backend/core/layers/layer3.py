"""
Layer 3: Research Agents Layer (Enhanced with Gemini AI)
Handles multi-agent reasoning, research coordination, and consensus building with AI-powered agents
"""

import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from .base import BaseLayer, LayerResult, register_layer
from core.memory import InMemoryKnowledgeGraph
from core.gemini_service import gemini_service, GeminiRequest, GeminiModel

@register_layer(3)
class Layer3ResearchAgents(BaseLayer):
    """
    Multi-agent research layer. Spawns and coordinates AI-powered research agents
    for complex reasoning, hypothesis generation, and consensus building.
    """
    
    def __init__(self):
        super().__init__()
        self.layer_number = 3
        self.layer_name = "Research Agents Layer"
        self.confidence_threshold = 0.995
        self.requires_agents = True
        self.requires_memory = True
        self.requires_ai = True
        
    def process(
        self, 
        input_data: Dict[str, Any], 
        state: Dict[str, Any], 
        memory: InMemoryKnowledgeGraph,
        agents: Optional[List[Any]] = None
    ) -> LayerResult:
        """Process multi-agent research and reasoning with AI-powered agents"""
        
        query = input_data.get("normalized_query", input_data.get("query", ""))
        complexity = input_data.get("complexity", 0.5)
        knowledge_available = input_data.get("knowledge_available", False)
        session_id = state.get("session_id")
        
        # Determine research strategy based on available knowledge and complexity
        research_strategy = self._determine_research_strategy(
            complexity, knowledge_available, input_data
        )
        
        # Spawn appropriate research agents
        research_agents = self._spawn_research_agents(research_strategy, query, state)
        
        # Coordinate AI-powered agent research
        agent_results = asyncio.run(self._coordinate_ai_agent_research(
            research_agents, input_data, memory, session_id
        ))
        
        # Analyze agent consensus and conflicts
        consensus_analysis = self._analyze_agent_consensus(agent_results)
        
        # Detect and handle forks if agents significantly disagree
        forks = self._detect_reasoning_forks(agent_results, consensus_analysis)
        
        # Generate final research output using AI synthesis
        research_output = asyncio.run(self._ai_synthesize_results(
            agent_results, consensus_analysis, input_data, session_id
        ))
        
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
            "evidence_quality": research_output.get("evidence_quality", "medium"),
            "ai_synthesis": research_output.get("synthesis_reasoning", "")
        }
        
        trace = {
            "research_strategy": research_strategy,
            "agents_spawned": len(research_agents),
            "consensus_reached": consensus_analysis["consensus_strength"] > 0.7,
            "major_disagreements": consensus_analysis["major_disagreement"],
            "forks_detected": len(forks),
            "ai_enhanced": True,
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
            metadata={
                "research_layer": True, 
                "agent_count": len(research_agents),
                "ai_enhanced": True
            }
        )
    
    def _determine_research_strategy(
        self, 
        complexity: float, 
        knowledge_available: bool, 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine the research strategy based on query characteristics"""
        
        query_type = input_data.get("query_type", "general")
        domain = input_data.get("domain", "general")
        safety_level = input_data.get("safety_level", "safe")
        
        strategy = {
            "approach": "collaborative",
            "agent_count": 3,
            "research_depth": "medium",
            "consensus_requirement": 0.7,
            "specialization_needed": False,
            "ai_temperature": 0.7,
            "parallel_processing": True
        }
        
        # Adjust based on complexity
        if complexity > 0.7:
            strategy["agent_count"] = 5
            strategy["research_depth"] = "deep"
            strategy["consensus_requirement"] = 0.8
            strategy["ai_temperature"] = 0.6  # More focused for complex queries
        elif complexity < 0.3:
            strategy["agent_count"] = 2
            strategy["research_depth"] = "shallow"
            strategy["ai_temperature"] = 0.8  # More creative for simple queries
        
        # Adjust based on query type
        if query_type == "risk_assessment":
            strategy["specialization_needed"] = True
            strategy["agent_count"] += 1  # Add safety specialist
            strategy["consensus_requirement"] = 0.9
            strategy["ai_temperature"] = 0.4  # Conservative for safety
        elif query_type == "analysis":
            strategy["approach"] = "multi_perspective"
            strategy["agent_count"] = 4
        elif query_type == "creative":
            strategy["ai_temperature"] = 0.9  # High creativity
            strategy["consensus_requirement"] = 0.6  # Allow more divergence
        
        return strategy
    
    def _spawn_research_agents(
        self, 
        strategy: Dict[str, Any], 
        query: str, 
        state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Spawn AI-powered research agents based on strategy"""
        
        agents = []
        agent_count = strategy["agent_count"]
        
        # Enhanced agent personas with AI specializations
        base_personas = [
            {
                "persona": "domain_expert", 
                "role": "Expert analysis and fact-checking",
                "ai_prompt_style": "analytical and precise",
                "temperature": 0.5
            },
            {
                "persona": "critical_thinker", 
                "role": "Challenge assumptions and find flaws",
                "ai_prompt_style": "skeptical and probing",
                "temperature": 0.6
            },
            {
                "persona": "creative_reasoner", 
                "role": "Generate alternative perspectives",
                "ai_prompt_style": "innovative and divergent",
                "temperature": 0.9
            },
            {
                "persona": "synthesizer", 
                "role": "Combine insights and build consensus",
                "ai_prompt_style": "integrative and balanced",
                "temperature": 0.7
            },
            {
                "persona": "safety_analyst", 
                "role": "Identify risks and safety concerns",
                "ai_prompt_style": "cautious and thorough",
                "temperature": 0.3
            }
        ]
        
        # Select appropriate personas
        selected_personas = base_personas[:agent_count]
        
        # Create agent instances
        for i, persona_info in enumerate(selected_personas):
            agent = {
                "id": f"research_agent_{uuid.uuid4().hex[:8]}",
                "persona": persona_info["persona"],
                "role": persona_info["role"],
                "ai_prompt_style": persona_info["ai_prompt_style"],
                "temperature": persona_info["temperature"],
                "query_focus": query,
                "strategy": strategy,
                "spawned_at": datetime.now().isoformat(),
                "active": True
            }
            agents.append(agent)
        
        return agents
    
    async def _coordinate_ai_agent_research(
        self, 
        agents: List[Dict[str, Any]], 
        input_data: Dict[str, Any], 
        memory: InMemoryKnowledgeGraph,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Coordinate AI-powered research across all agents"""
        
        # Create tasks for parallel processing
        tasks = []
        for agent in agents:
            task = self._ai_agent_research(agent, input_data, memory, session_id)
            tasks.append(task)
        
        # Execute all agent research in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid results
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Create fallback result for failed agents
                valid_results.append({
                    "agent_id": agents[i]["id"],
                    "persona": agents[i]["persona"],
                    "answer": f"Agent processing failed: {str(result)}",
                    "confidence": 0.1,
                    "reasoning": "AI agent encountered an error",
                    "error": True
                })
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def _ai_agent_research(
        self, 
        agent: Dict[str, Any], 
        input_data: Dict[str, Any], 
        memory: InMemoryKnowledgeGraph,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform AI-powered research for individual agent"""
        
        persona = agent["persona"]
        query = input_data.get("normalized_query", "")
        context = input_data.get("context", {})
        
        # Build persona-specific system prompt
        system_prompt = self._build_agent_system_prompt(agent, input_data)
        
        # Build research prompt
        research_prompt = self._build_research_prompt(agent, query, input_data, context)
        
        try:
            # Make AI request with persona-specific parameters
            request = GeminiRequest(
                prompt=research_prompt,
                system_prompt=system_prompt,
                model=GeminiModel.GEMINI_PRO,  # Use more powerful model for research
                temperature=agent.get("temperature", 0.7),
                persona=persona
            )
            
            response = await gemini_service.generate_async(
                request, 
                session_id=session_id, 
                layer=3
            )
            
            # Parse AI response
            analysis = self._parse_agent_response(response.content, agent)
            
            return {
                "agent_id": agent["id"],
                "persona": persona,
                "answer": analysis.get("answer", response.content),
                "confidence": analysis.get("confidence", response.confidence),
                "reasoning": analysis.get("reasoning", "AI reasoning provided"),
                "evidence": analysis.get("evidence", []),
                "alternatives": analysis.get("alternatives", []),
                "ai_response": response.content,
                "processing_time": response.processing_time
            }
            
        except Exception as e:
            # Fallback for failed AI requests
            return {
                "agent_id": agent["id"],
                "persona": persona,
                "answer": f"Research failed: {str(e)}",
                "confidence": 0.1,
                "reasoning": "AI agent failed to process request",
                "error": True,
                "error_message": str(e)
            }
    
    def _build_agent_system_prompt(self, agent: Dict[str, Any], input_data: Dict[str, Any]) -> str:
        """Build system prompt for specific agent persona"""
        
        persona = agent["persona"]
        role = agent["role"]
        style = agent.get("ai_prompt_style", "analytical")
        
        base_prompt = f"""
        You are a research agent in a multi-layered AI simulation system.
        
        PERSONA: {persona}
        ROLE: {role}
        STYLE: {style}
        
        Your task is to analyze the given query from your specific perspective.
        Provide thorough, accurate analysis while maintaining your persona characteristics.
        
        IMPORTANT: Provide your response in JSON format with these fields:
        - answer: Your main response/analysis
        - confidence: Your confidence level (0.0-1.0)
        - reasoning: Explanation of your analytical process
        - evidence: List of key evidence points
        - alternatives: Alternative viewpoints or solutions
        - concerns: Any concerns or limitations from your perspective
        """
        
        # Add persona-specific instructions
        if persona == "domain_expert":
            base_prompt += "\nFocus on accuracy, facts, and domain-specific knowledge."
        elif persona == "critical_thinker":
            base_prompt += "\nChallenge assumptions, identify weaknesses, and ask probing questions."
        elif persona == "creative_reasoner":
            base_prompt += "\nExplore unconventional approaches and generate innovative solutions."
        elif persona == "synthesizer":
            base_prompt += "\nIntegrate different viewpoints and find common ground."
        elif persona == "safety_analyst":
            base_prompt += "\nPrioritize safety, risk assessment, and potential negative consequences."
        
        return base_prompt
    
    def _build_research_prompt(
        self, 
        agent: Dict[str, Any], 
        query: str, 
        input_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> str:
        """Build research prompt for agent"""
        
        prompt = f"""
        RESEARCH QUERY: {query}
        
        CONTEXT INFORMATION:
        - Query Type: {input_data.get('query_type', 'unknown')}
        - Complexity: {input_data.get('complexity', 0.5)}
        - Domain: {input_data.get('domain', 'general')}
        - Safety Level: {input_data.get('safety_level', 'safe')}
        
        ADDITIONAL CONTEXT:
        {context}
        
        Please analyze this query thoroughly from your perspective as a {agent['persona']}.
        Consider all relevant factors and provide comprehensive analysis.
        
        Remember to format your response as valid JSON with all required fields.
        """
        
        return prompt
    
    def _parse_agent_response(self, response_text: str, agent: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI agent response, with fallback for non-JSON responses"""
        
        try:
            import json
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback parsing for non-JSON responses
            return {
                "answer": response_text,
                "confidence": 0.8,
                "reasoning": f"Response from {agent['persona']} agent",
                "evidence": [],
                "alternatives": [],
                "concerns": []
            }
    
    async def _ai_synthesize_results(
        self,
        agent_results: List[Dict[str, Any]],
        consensus_analysis: Dict[str, Any],
        input_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Use AI to synthesize all agent results into final research output"""
        
        # Prepare synthesis prompt
        synthesis_prompt = self._build_synthesis_prompt(agent_results, consensus_analysis, input_data)
        
        try:
            request = GeminiRequest(
                prompt=synthesis_prompt,
                system_prompt="""
                You are a research synthesis expert. Your job is to analyze multiple agent perspectives
                and create a comprehensive, balanced final answer. Consider all viewpoints, identify
                areas of agreement and disagreement, and provide a well-reasoned conclusion.
                
                Respond in JSON format with:
                - answer: Final synthesized answer
                - confidence: Overall confidence level
                - evidence_quality: Assessment of evidence strength
                - alternatives: Alternative viewpoints to consider
                - synthesis_reasoning: Your reasoning process
                - requires_expert_review: Boolean if human expert review is needed
                """,
                model=GeminiModel.GEMINI_PRO,
                temperature=0.6  # Balanced temperature for synthesis
            )
            
            response = await gemini_service.generate_async(
                request, 
                session_id=session_id, 
                layer=3
            )
            
            # Parse synthesis response
            try:
                import json
                synthesis = json.loads(response.content)
                return synthesis
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "answer": response.content,
                    "confidence": response.confidence,
                    "evidence_quality": "medium",
                    "alternatives": [],
                    "synthesis_reasoning": "AI synthesis provided",
                    "requires_expert_review": False
                }
                
        except Exception as e:
            # Fallback synthesis
            return self._fallback_synthesis(agent_results, consensus_analysis)
    
    def _build_synthesis_prompt(
        self,
        agent_results: List[Dict[str, Any]],
        consensus_analysis: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> str:
        """Build prompt for AI synthesis of agent results"""
        
        query = input_data.get("normalized_query", "")
        
        # Format agent results for synthesis
        agent_summaries = []
        for result in agent_results:
            if not result.get("error", False):
                summary = f"""
                AGENT: {result['persona']}
                ANSWER: {result['answer']}
                CONFIDENCE: {result['confidence']}
                REASONING: {result['reasoning']}
                """
                agent_summaries.append(summary)
        
        consensus_info = f"""
        CONSENSUS ANALYSIS:
        - Consensus Strength: {consensus_analysis.get('consensus_strength', 0.0)}
        - Major Disagreement: {consensus_analysis.get('major_disagreement', False)}
        - Agreement Areas: {consensus_analysis.get('agreement_areas', [])}
        - Disagreement Areas: {consensus_analysis.get('disagreement_areas', [])}
        """
        
        prompt = f"""
        ORIGINAL QUERY: {query}
        
        AGENT RESEARCH RESULTS:
        {chr(10).join(agent_summaries)}
        
        {consensus_info}
        
        Please synthesize these multiple agent perspectives into a comprehensive final answer.
        Consider the strengths and weaknesses of each perspective, areas of agreement and disagreement,
        and provide a balanced, well-reasoned conclusion.
        
        Format your response as valid JSON with all required fields.
        """
        
        return prompt
    
    def _fallback_synthesis(
        self,
        agent_results: List[Dict[str, Any]],
        consensus_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback synthesis when AI fails"""
        
        # Simple majority voting
        answers = [r["answer"] for r in agent_results if not r.get("error", False)]
        confidences = [r["confidence"] for r in agent_results if not r.get("error", False)]
        
        if not answers:
            return {
                "answer": "No valid agent results available",
                "confidence": 0.1,
                "evidence_quality": "poor",
                "alternatives": [],
                "synthesis_reasoning": "Fallback synthesis - no valid results",
                "requires_expert_review": True
            }
        
        # Use highest confidence answer as primary
        best_idx = confidences.index(max(confidences))
        primary_answer = answers[best_idx]
        avg_confidence = sum(confidences) / len(confidences)
        
        return {
            "answer": primary_answer,
            "confidence": avg_confidence,
            "evidence_quality": "medium",
            "alternatives": [a for a in answers if a != primary_answer],
            "synthesis_reasoning": "Rule-based synthesis using highest confidence result",
            "requires_expert_review": avg_confidence < 0.8
        }
    
    def _analyze_agent_consensus(self, agent_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze consensus and disagreements among agents"""
        
        valid_results = [r for r in agent_results if not r.get("error", False)]
        
        if len(valid_results) < 2:
            return {
                "consensus_strength": 0.0,
                "major_disagreement": True,
                "agreement_areas": [],
                "disagreement_areas": ["Insufficient valid agent results"],
                "confidence_spread": 1.0
            }
        
        # Calculate confidence spread
        confidences = [r["confidence"] for r in valid_results]
        confidence_spread = max(confidences) - min(confidences)
        
        # Simple consensus analysis (could be enhanced with semantic similarity)
        answers = [str(r["answer"]).lower() for r in valid_results]
        unique_answers = len(set(answers))
        consensus_strength = 1.0 - (unique_answers - 1) / len(answers)
        
        major_disagreement = confidence_spread > 0.3 or consensus_strength < 0.5
        
        return {
            "consensus_strength": consensus_strength,
            "major_disagreement": major_disagreement,
            "agreement_areas": ["Basic analysis"] if consensus_strength > 0.7 else [],
            "disagreement_areas": ["Specific conclusions"] if major_disagreement else [],
            "confidence_spread": confidence_spread,
            "valid_agents": len(valid_results)
        }
    
    def _detect_reasoning_forks(
        self, 
        agent_results: List[Dict[str, Any]], 
        consensus_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect reasoning forks based on agent disagreements"""
        
        forks = []
        
        if consensus_analysis["major_disagreement"]:
            # Group agents by similar answers (simplified)
            answer_groups = {}
            for result in agent_results:
                if result.get("error", False):
                    continue
                    
                answer_key = str(result["answer"])[:100]  # First 100 chars as key
                if answer_key not in answer_groups:
                    answer_groups[answer_key] = []
                answer_groups[answer_key].append(result)
            
            # Create forks for significant disagreements
            if len(answer_groups) > 1:
                for answer_key, group in answer_groups.items():
                    if len(group) >= 1:  # At least one agent supports this view
                        fork = {
                            "id": str(uuid.uuid4()),
                            "type": "agent_disagreement",
                            "reason": f"Agent reasoning divergence: {len(group)} agents support this view",
                            "supporting_agents": [r["agent_id"] for r in group],
                            "alternative_answer": group[0]["answer"],
                            "confidence": sum(r["confidence"] for r in group) / len(group)
                        }
                        forks.append(fork)
        
        return forks
    
    def _calculate_research_confidence(
        self,
        agent_results: List[Dict[str, Any]],
        consensus_analysis: Dict[str, Any],
        research_output: Dict[str, Any]
    ) -> float:
        """Calculate overall research confidence"""
        
        valid_results = [r for r in agent_results if not r.get("error", False)]
        
        if not valid_results:
            return 0.1
        
        # Base confidence from agents
        agent_confidences = [r["confidence"] for r in valid_results]
        avg_agent_confidence = sum(agent_confidences) / len(agent_confidences)
        
        # Adjust based on consensus
        consensus_bonus = consensus_analysis["consensus_strength"] * 0.1
        
        # Adjust based on synthesis quality
        synthesis_confidence = research_output.get("confidence", avg_agent_confidence)
        
        # Penalize for errors
        error_penalty = len([r for r in agent_results if r.get("error", False)]) * 0.05
        
        final_confidence = (
            avg_agent_confidence * 0.4 +
            synthesis_confidence * 0.4 +
            consensus_bonus * 0.2 -
            error_penalty
        )
        
        return max(0.1, min(1.0, final_confidence))
