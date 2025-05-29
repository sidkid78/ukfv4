"""
Layer 3: Research Agents Layer
Handles multi-agent reasoning, research coordination, and consensus building
"""

import uuid
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base import BaseLayer, LayerResult, register_layer
from core.memory import InMemoryKnowledgeGraph
from core.gemini_service import gemini_service, GeminiRequest, GeminiModel
import asyncio


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
        self.confidence_threshold = 0.85  # More realistic threshold
        self.requires_agents = True
        self.requires_memory = True
        self.logger = logging.getLogger(__name__)
        self.log_dir = Path("logs/layer3")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def process(self, input_data: Dict[str, Any], state: Dict[str, Any], 
               memory: InMemoryKnowledgeGraph, agents: Optional[List[Any]] = None) -> LayerResult:
        """Process multi-agent research and reasoning"""
        process_id = uuid.uuid4().hex[:8]
        self.logger.info(f"Starting research process {process_id} for query: {input_data.get('query', '')}")
        self._save_artifact({"process_start": datetime.now().isoformat(), "input_data": input_data}, 
                          f"process_start_{process_id}.json")
        
        try:
            query = input_data.get("normalized_query", input_data.get("query", ""))
            complexity = input_data.get("complexity", 0.5)
            knowledge_available = input_data.get("knowledge_available", False)
            
            self._log_input_data(input_data, process_id)
            
            research_strategy = self._determine_research_strategy(complexity, knowledge_available, input_data)
            self.logger.debug(f"Research strategy determined: {json.dumps(research_strategy, indent=2)}")
            self._save_artifact(research_strategy, f"strategy_{process_id}.json")
            
            research_agents = self._spawn_research_agents(research_strategy, query, state)
            self.logger.info(f"Spawned {len(research_agents)} research agents: {[a['persona'] for a in research_agents]}")
            self._save_artifact({
                "agents": research_agents,
                "spawn_timestamp": datetime.now().isoformat()
            }, f"agents_{process_id}.json")
            
            agent_results = self._coordinate_agent_research(research_agents, input_data, memory)
            self.logger.info(f"Completed agent research with {len(agent_results)} results")
            self._save_artifact({
                "results": agent_results,
                "research_metrics": self._calculate_research_metrics(agent_results)
            }, f"results_{process_id}.json")
            
            consensus_analysis = self._analyze_agent_consensus(agent_results)
            self.logger.info(f"Consensus analysis: {consensus_analysis['agreement_level']} agreement")
            self._save_artifact(consensus_analysis, f"consensus_{process_id}.json")
            
            forks = self._detect_reasoning_forks(agent_results, consensus_analysis)
            if forks:
                self.logger.warning(f"Detected {len(forks)} reasoning forks requiring resolution")
                self._save_artifact({
                    "forks": forks,
                    "detection_time": datetime.now().isoformat()
                }, f"forks_{process_id}.json")
                self.logger.debug(f"Fork details: {json.dumps(forks, indent=2)}")
            
            research_output = self._synthesize_agent_results(agent_results, consensus_analysis, input_data)
            self.logger.info(f"Research output synthesized with confidence {research_output.get('confidence', 0):.2f}")
            self._save_artifact(research_output, f"output_{process_id}.json")
            
            confidence = self._calculate_research_confidence(agent_results, consensus_analysis, research_output)
            # Only escalate on low confidence, major disagreement with low consensus, or explicit expert review requirement
            escalate = (self.should_escalate(confidence) or 
                       (consensus_analysis["major_disagreement"] and consensus_analysis["consensus_strength"] < 0.4) or
                       (research_output.get("requires_expert_review", False) and confidence < 0.8))
            
            output = self._prepare_output(input_data, research_strategy, agent_results, 
                                        consensus_analysis, research_output)
            trace = self._prepare_trace(research_strategy, research_agents, consensus_analysis, forks, agent_results)
            
            self.logger.info(f"Research process {process_id} completed with confidence {confidence:.2f}")
            self._save_artifact({
                "final_output": output,
                "confidence": confidence,
                "escalate": escalate,
                "completion_time": datetime.now().isoformat()
            }, f"final_output_{process_id}.json")
            
            return LayerResult(
                output=output,
                confidence=confidence,
                escalate=escalate,
                trace=trace,
                forks=forks,
                agents_spawned=[agent["id"] for agent in research_agents],
                metadata={"research_layer": True, "agent_count": len(research_agents)}
            )
            
        except Exception as e:
            self.logger.error(f"Research process {process_id} failed: {str(e)}", exc_info=True)
            self._save_artifact({
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, f"error_{process_id}.json")
            raise
    
    def _log_input_data(self, input_data: Dict[str, Any], process_id: str) -> None:
        """Log and save input data for auditing"""
        sanitized_data = {k: v for k, v in input_data.items() if not isinstance(v, (bytes, type))}
        self.logger.debug(f"Process {process_id} input data: {json.dumps(sanitized_data, indent=2)}")
        self._save_artifact(sanitized_data, f"input_{process_id}.json")
    
    def _save_artifact(self, data: Any, filename: str) -> None:
        """Save research artifact to file"""
        try:
            filepath = self.log_dir / filename
            with open(filepath, 'w') as f:
                if isinstance(data, (dict, list)):
                    json.dump(data, f, indent=2)
                else:
                    f.write(str(data))
            self.logger.debug(f"Saved artifact to {filepath}")
        except IOError as e:
            self.logger.error(f"Failed to save artifact {filename}: {str(e)}")
    
    def _prepare_output(self, input_data: Dict[str, Any], research_strategy: Dict[str, Any],
                      agent_results: List[Dict[str, Any]], consensus_analysis: Dict[str, Any],
                      research_output: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare final output structure"""
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
        self.logger.debug(f"Prepared output structure: {json.dumps(output, indent=2)}")
        return output
    
    def _prepare_trace(self, research_strategy: Dict[str, Any], research_agents: List[Dict[str, Any]],
                     consensus_analysis: Dict[str, Any], forks: List[Dict[str, Any]],
                     agent_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare tracing information"""
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
        self.logger.debug(f"Prepared trace data: {json.dumps(trace, indent=2)}")
        return trace

    def _spawn_research_agents(self, strategy: Dict[str, Any], query: str, 
                              state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Spawn research agents based on strategy"""
        self.logger.info(f"Spawning agents with strategy: {strategy['approach']}")
        agents = []
        
        base_personas = [
            {"persona": "domain_expert", "role": "Expert analysis and fact-checking"},
            {"persona": "critical_thinker", "role": "Challenge assumptions and find flaws"},
            {"persona": "creative_reasoner", "role": "Generate alternative perspectives"},
            {"persona": "synthesizer", "role": "Combine insights and build consensus"},
            {"persona": "safety_analyst", "role": "Identify risks and safety concerns"}
        ]
        
        selected_personas = base_personas[:strategy["agent_count"]]
        self.logger.debug(f"Base personas selected: {[p['persona'] for p in selected_personas]}")
        
        if strategy.get("specialization_needed", False):
            selected_personas.append({
                "persona": "risk_specialist", 
                "role": "Deep risk analysis and mitigation"
            })
            self.logger.debug("Added risk specialist agent")
        
        self._save_artifact({"selected_personas": selected_personas}, "persona_selection.json")
        
        for persona_info in selected_personas:
            agent_id = f"research_agent_{uuid.uuid4().hex[:8]}"
            agent = {
                "id": agent_id,
                "persona": persona_info["persona"],
                "role": persona_info["role"],
                "query_focus": query,
                "strategy": strategy,
                "spawned_at": datetime.now().isoformat(),
                "active": True
            }
            self.logger.debug(f"Created agent {agent_id} as {persona_info['persona']}")
            agents.append(agent)
            self._save_artifact(agent, f"agent_{agent_id}.json")
            
        return agents
    
    def _coordinate_agent_research(self, agents: List[Dict[str, Any]], 
                                  input_data: Dict[str, Any], 
                                  memory: InMemoryKnowledgeGraph) -> List[Dict[str, Any]]:
        """Coordinate research across all agents"""
        self.logger.info(f"Coordinating research for {len(agents)} agents")
        results = []
        
        for agent in agents:
            self.logger.debug(f"Starting research for agent {agent['id']}")
            start_time = datetime.now()
            
            agent_result = self._simulate_agent_research(agent, input_data, memory)
            
            research_time = (datetime.now() - start_time).total_seconds()
            agent_result["research_time"] = research_time
            self.logger.debug(f"Agent {agent['id']} completed research in {research_time:.2f}s")
            results.append(agent_result)
            self._save_artifact(agent_result, f"agent_result_{agent['id']}.json")
            
        return results
    
    def _simulate_agent_research(
        self, 
        agent: Dict[str, Any], 
        input_data: Dict[str, Any], 
        memory: InMemoryKnowledgeGraph
    ) -> Dict[str, Any]:
        """Simulate individual agent research process"""
        self.logger.debug(f"Simulating research for {agent['persona']} agent {agent['id']}")
        persona = agent["persona"]
        query = input_data.get("normalized_query", "")
        
        analysis_methods = {
            "domain_expert": self._expert_analysis,
            "critical_thinker": self._critical_analysis,
            "creative_reasoner": self._creative_analysis,
            "synthesizer": self._synthesis_analysis,
            "safety_analyst": self._safety_analysis,
            "risk_specialist": self._safety_analysis
        }
        
        analysis_func = analysis_methods.get(persona, self._general_analysis)
        answer, confidence, reasoning = analysis_func(query, input_data, memory)
        
        self.logger.debug(f"{persona} agent {agent['id']} generated answer with confidence {confidence:.2f}")
        
        return {
            "agent_id": agent["id"],
            "persona": persona,
            "answer": answer,
            "confidence": confidence,
            "reasoning": reasoning,
            "research_time": 0.5,
            "evidence_strength": "medium",
            "alternative_considered": True
        }
    
    def _expert_analysis(self, query: str, input_data: Dict[str, Any], memory) -> tuple:
        """Domain expert analysis approach using real AI"""
        self.logger.debug(f"Performing AI-powered expert analysis on: {query}")
        
        # Build context from available knowledge
        knowledge_available = input_data.get("knowledge_available", False)
        context = {
            "query": query,
            "knowledge_available": knowledge_available,
            "memory_data": input_data.get("memory_answer") if knowledge_available else None,
            "complexity": input_data.get("complexity", 0.5)
        }
        
        # Create AI request for domain expert analysis
        ai_request = GeminiRequest(
            prompt=f"As a domain expert, analyze this query and provide expert insights: {query}",
            system_prompt="""You are a domain expert providing comprehensive analysis. 
            Provide detailed, evidence-based insights with specific reasoning. 
            Focus on accuracy, depth, and actionable conclusions.
            Format your response as: ANALYSIS: [your analysis] | CONFIDENCE: [0.0-1.0] | REASONING: [your reasoning]""",
            persona="domain_expert",
            context=context,
            model=GeminiModel.GEMINI_FLASH_0520,
            temperature=0.3  # Lower temperature for expert analysis
        )
        
        try:
            # Make async call to Gemini
            response = asyncio.run(gemini_service.generate_async(ai_request))
            
            # Parse the structured response
            content = response.content
            confidence = response.confidence
            
            # Try to extract structured information
            if "ANALYSIS:" in content and "CONFIDENCE:" in content:
                parts = content.split("|") 
                analysis_part = next((p.strip() for p in parts if p.strip().startswith("ANALYSIS:")), "")
                conf_part = next((p.strip() for p in parts if p.strip().startswith("CONFIDENCE:")), "")
                reasoning_part = next((p.strip() for p in parts if p.strip().startswith("REASONING:")), "")
                
                answer = analysis_part.replace("ANALYSIS:", "").strip() if analysis_part else content
                
                # Extract confidence if provided
                if conf_part:
                    try:
                        ai_confidence = float(conf_part.replace("CONFIDENCE:", "").strip())
                        confidence = min(0.99, max(0.1, ai_confidence))
                    except ValueError:
                        pass
                        
                reasoning = reasoning_part.replace("REASONING:", "").strip() if reasoning_part else "AI-powered domain expert analysis"
            else:
                answer = content
                reasoning = "AI-powered domain expert analysis"
            
            # Boost confidence if we have good knowledge available
            if knowledge_available and input_data.get("memory_answer"):
                confidence = min(0.95, confidence + 0.1)
                answer = f"Expert analysis (with knowledge base): {answer}"
            
            self.logger.info(f"Expert AI analysis complete - confidence: {confidence:.2f}")
            return answer, confidence, reasoning
            
        except Exception as e:
            self.logger.error(f"Expert AI analysis failed: {str(e)}")
            # Fallback to basic response
            return f"Expert analysis of '{query}' (AI temporarily unavailable)", 0.6, f"Fallback analysis due to AI error: {str(e)}"
    
    def _critical_analysis(self, query: str, input_data: Dict[str, Any], memory) -> tuple:
        """Critical thinking analysis approach using real AI"""
        self.logger.debug(f"Performing AI-powered critical analysis on: {query}")
        
        context = {
            "query": query,
            "complexity": input_data.get("complexity", 0.5),
            "memory_data": input_data.get("memory_answer", "No prior knowledge available")
        }
        
        ai_request = GeminiRequest(
            prompt=f"As a critical thinker, analyze this query and identify assumptions, biases, and potential flaws: {query}",
            system_prompt="""You are a critical thinking expert. Challenge assumptions, identify biases, 
            look for logical fallacies, and point out areas that need validation or further evidence.
            Be thorough but constructive in your criticism.
            Format: ANALYSIS: [critical analysis] | CONFIDENCE: [0.0-1.0] | REASONING: [your reasoning]""",
            persona="critical_thinker",
            context=context,
            model=GeminiModel.GEMINI_FLASH,
            temperature=0.5  # Medium temperature for balanced critical thinking
        )
        
        try:
            response = asyncio.run(gemini_service.generate_async(ai_request))
            content = response.content
            confidence = response.confidence
            
            # Parse structured response
            if "ANALYSIS:" in content and "CONFIDENCE:" in content:
                parts = content.split("|")
                analysis_part = next((p.strip() for p in parts if p.strip().startswith("ANALYSIS:")), "")
                conf_part = next((p.strip() for p in parts if p.strip().startswith("CONFIDENCE:")), "")
                reasoning_part = next((p.strip() for p in parts if p.strip().startswith("REASONING:")), "")
                
                answer = analysis_part.replace("ANALYSIS:", "").strip() if analysis_part else content
                
                if conf_part:
                    try:
                        ai_confidence = float(conf_part.replace("CONFIDENCE:", "").strip())
                        confidence = min(0.99, max(0.1, ai_confidence))
                    except ValueError:
                        pass
                        
                reasoning = reasoning_part.replace("REASONING:", "").strip() if reasoning_part else "AI-powered critical analysis"
            else:
                answer = content
                reasoning = "AI-powered critical analysis"
            
            self.logger.info(f"Critical AI analysis complete - confidence: {confidence:.2f}")
            return answer, confidence, reasoning
            
        except Exception as e:
            self.logger.error(f"Critical AI analysis failed: {str(e)}")
            return f"Critical analysis of '{query}' reveals areas requiring deeper examination (AI temporarily unavailable)", 0.65, f"Fallback critical analysis: {str(e)}"
    
    def _creative_analysis(self, query: str, input_data: Dict[str, Any], memory) -> tuple:
        """Creative reasoning analysis approach using real AI"""
        self.logger.debug(f"Performing AI-powered creative analysis on: {query}")
        
        context = {
            "query": query,
            "complexity": input_data.get("complexity", 0.5),
            "existing_perspective": input_data.get("memory_answer", "Standard approach")
        }
        
        ai_request = GeminiRequest(
            prompt=f"Think creatively about this query and provide alternative perspectives, unconventional approaches, and innovative solutions: {query}",
            system_prompt="""You are a creative reasoning expert. Think outside the box, generate novel ideas, 
            consider unconventional approaches, and propose innovative solutions. Be imaginative but grounded.
            Format: ANALYSIS: [creative insights] | CONFIDENCE: [0.0-1.0] | REASONING: [your reasoning]""",
            persona="creative_reasoner",
            context=context,
            model=GeminiModel.GEMINI_FLASH,
            temperature=0.8  # Higher temperature for creativity
        )
        
        try:
            response = asyncio.run(gemini_service.generate_async(ai_request))
            content = response.content
            confidence = response.confidence
            
            # Parse structured response
            if "ANALYSIS:" in content and "CONFIDENCE:" in content:
                parts = content.split("|")
                analysis_part = next((p.strip() for p in parts if p.strip().startswith("ANALYSIS:")), "")
                conf_part = next((p.strip() for p in parts if p.strip().startswith("CONFIDENCE:")), "")
                reasoning_part = next((p.strip() for p in parts if p.strip().startswith("REASONING:")), "")
                
                answer = analysis_part.replace("ANALYSIS:", "").strip() if analysis_part else content
                
                if conf_part:
                    try:
                        ai_confidence = float(conf_part.replace("CONFIDENCE:", "").strip())
                        confidence = min(0.99, max(0.1, ai_confidence))
                    except ValueError:
                        pass
                        
                reasoning = reasoning_part.replace("REASONING:", "").strip() if reasoning_part else "AI-powered creative analysis"
            else:
                answer = content
                reasoning = "AI-powered creative analysis"
            
            self.logger.info(f"Creative AI analysis complete - confidence: {confidence:.2f}")
            return answer, confidence, reasoning
            
        except Exception as e:
            self.logger.error(f"Creative AI analysis failed: {str(e)}")
            return f"Creative perspective on '{query}': Consider exploring unconventional approaches (AI temporarily unavailable)", 0.6, f"Fallback creative analysis: {str(e)}"
    
    def _synthesis_analysis(self, query: str, input_data: Dict[str, Any], memory) -> tuple:
        """Synthesis analysis approach using real AI"""
        self.logger.debug(f"Performing AI-powered synthesis analysis on: {query}")
        
        # Gather all available perspectives for synthesis
        context = {
            "query": query,
            "memory_data": input_data.get("memory_answer", "No prior knowledge"),
            "complexity": input_data.get("complexity", 0.5),
            "available_knowledge": input_data.get("knowledge_available", False)
        }
        
        ai_request = GeminiRequest(
            prompt=f"Synthesize and integrate multiple perspectives on this query to provide a comprehensive, balanced analysis: {query}",
            system_prompt="""You are a synthesis expert who combines insights from multiple sources and perspectives. 
            Integrate different viewpoints, identify patterns, and provide comprehensive conclusions.
            Balance depth with clarity and ensure all major aspects are covered.
            Format: ANALYSIS: [synthesized insights] | CONFIDENCE: [0.0-1.0] | REASONING: [your reasoning]""",
            persona="synthesizer",
            context=context,
            model=GeminiModel.GEMINI_FLASH_0520,
            temperature=0.4  # Balanced temperature for synthesis
        )
        
        try:
            response = asyncio.run(gemini_service.generate_async(ai_request))
            content = response.content
            confidence = response.confidence
            
            # Parse structured response
            if "ANALYSIS:" in content and "CONFIDENCE:" in content:
                parts = content.split("|")
                analysis_part = next((p.strip() for p in parts if p.strip().startswith("ANALYSIS:")), "")
                conf_part = next((p.strip() for p in parts if p.strip().startswith("CONFIDENCE:")), "")
                reasoning_part = next((p.strip() for p in parts if p.strip().startswith("REASONING:")), "")
                
                answer = analysis_part.replace("ANALYSIS:", "").strip() if analysis_part else content
                
                if conf_part:
                    try:
                        ai_confidence = float(conf_part.replace("CONFIDENCE:", "").strip())
                        confidence = min(0.99, max(0.1, ai_confidence))
                    except ValueError:
                        pass
                        
                reasoning = reasoning_part.replace("REASONING:", "").strip() if reasoning_part else "AI-powered synthesis analysis"
            else:
                answer = content
                reasoning = "AI-powered synthesis analysis"
            
            # Boost confidence for synthesis (it combines multiple perspectives)
            confidence = min(0.95, confidence + 0.05)
            
            self.logger.info(f"Synthesis AI analysis complete - confidence: {confidence:.2f}")
            return answer, confidence, reasoning
            
        except Exception as e:
            self.logger.error(f"Synthesis AI analysis failed: {str(e)}")
            return f"Synthesized understanding of '{query}' integrating available perspectives (AI temporarily unavailable)", 0.75, f"Fallback synthesis: {str(e)}"
    
    def _safety_analysis(self, query: str, input_data: Dict[str, Any], memory) -> tuple:
        """Safety and risk analysis approach using real AI"""
        self.logger.debug(f"Performing AI-powered safety analysis on: {query}")
        
        context = {
            "query": query,
            "complexity": input_data.get("complexity", 0.5),
            "context_available": bool(input_data.get("memory_answer"))
        }
        
        ai_request = GeminiRequest(
            prompt=f"Conduct a comprehensive safety and risk analysis of this query, identifying potential risks, safety concerns, and mitigation strategies: {query}",
            system_prompt="""You are a safety analysis expert focused on risk assessment and harm prevention. 
            Identify potential risks, safety concerns, ethical implications, and propose mitigation strategies.
            Be thorough in identifying both obvious and subtle risks.
            Format: ANALYSIS: [safety analysis] | CONFIDENCE: [0.0-1.0] | REASONING: [your reasoning]""",
            persona="safety_analyst",
            context=context,
            model=GeminiModel.GEMINI_FLASH,
            temperature=0.2  # Lower temperature for safety-critical analysis
        )
        
        try:
            response = asyncio.run(gemini_service.generate_async(ai_request))
            content = response.content
            confidence = response.confidence
            
            # Parse structured response
            if "ANALYSIS:" in content and "CONFIDENCE:" in content:
                parts = content.split("|")
                analysis_part = next((p.strip() for p in parts if p.strip().startswith("ANALYSIS:")), "")
                conf_part = next((p.strip() for p in parts if p.strip().startswith("CONFIDENCE:")), "")
                reasoning_part = next((p.strip() for p in parts if p.strip().startswith("REASONING:")), "")
                
                answer = analysis_part.replace("ANALYSIS:", "").strip() if analysis_part else content
                
                if conf_part:
                    try:
                        ai_confidence = float(conf_part.replace("CONFIDENCE:", "").strip())
                        confidence = min(0.99, max(0.1, ai_confidence))
                    except ValueError:
                        pass
                        
                reasoning = reasoning_part.replace("REASONING:", "").strip() if reasoning_part else "AI-powered safety analysis"
            else:
                answer = content
                reasoning = "AI-powered safety analysis"
            
            # Boost confidence for safety analysis (critical for safety)
            confidence = min(0.95, confidence + 0.08)
            
            self.logger.info(f"Safety AI analysis complete - confidence: {confidence:.2f}")
            return answer, confidence, reasoning
            
        except Exception as e:
            self.logger.error(f"Safety AI analysis failed: {str(e)}")
            return f"Safety analysis of '{query}' identifies potential risks requiring careful consideration (AI temporarily unavailable)", 0.7, f"Fallback safety analysis: {str(e)}"
    
    def _general_analysis(self, query: str, input_data: Dict[str, Any], memory) -> tuple:
        """General analysis approach using real AI"""
        self.logger.debug(f"Performing AI-powered general analysis on: {query}")
        
        context = {
            "query": query,
            "complexity": input_data.get("complexity", 0.5),
            "available_context": input_data.get("memory_answer", "No specific context available")
        }
        
        ai_request = GeminiRequest(
            prompt=f"Provide a comprehensive, balanced analysis of this query considering multiple factors and perspectives: {query}",
            system_prompt="""You are a general analysis expert providing balanced, comprehensive insights. 
            Consider multiple factors, provide balanced perspectives, and offer practical conclusions.
            Be thorough but accessible in your analysis.
            Format: ANALYSIS: [comprehensive analysis] | CONFIDENCE: [0.0-1.0] | REASONING: [your reasoning]""",
            persona="general_analyst",
            context=context,
            model=GeminiModel.GEMINI_FLASH,
            temperature=0.6  # Balanced temperature for general analysis
        )
        
        try:
            response = asyncio.run(gemini_service.generate_async(ai_request))
            content = response.content
            confidence = response.confidence
            
            # Parse structured response
            if "ANALYSIS:" in content and "CONFIDENCE:" in content:
                parts = content.split("|")
                analysis_part = next((p.strip() for p in parts if p.strip().startswith("ANALYSIS:")), "")
                conf_part = next((p.strip() for p in parts if p.strip().startswith("CONFIDENCE:")), "")
                reasoning_part = next((p.strip() for p in parts if p.strip().startswith("REASONING:")), "")
                
                answer = analysis_part.replace("ANALYSIS:", "").strip() if analysis_part else content
                
                if conf_part:
                    try:
                        ai_confidence = float(conf_part.replace("CONFIDENCE:", "").strip())
                        confidence = min(0.99, max(0.1, ai_confidence))
                    except ValueError:
                        pass
                        
                reasoning = reasoning_part.replace("REASONING:", "").strip() if reasoning_part else "AI-powered general analysis"
            else:
                answer = content
                reasoning = "AI-powered general analysis"
            
            self.logger.info(f"General AI analysis complete - confidence: {confidence:.2f}")
            return answer, confidence, reasoning
            
        except Exception as e:
            self.logger.error(f"General AI analysis failed: {str(e)}")
            return f"General analysis of '{query}' provides balanced perspective (AI temporarily unavailable)", 0.7, f"Fallback general analysis: {str(e)}"
    
    def _analyze_agent_consensus(self, agent_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze consensus and disagreement among agents"""
        self.logger.debug("Analyzing agent consensus")
        
        if not agent_results:
            return {"consensus_strength": 0.0, "major_disagreement": True}
        
        confidences = [r["confidence"] for r in agent_results]
        avg_confidence = sum(confidences) / len(confidences)
        confidence_variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)
        
        consensus_strength = max(0.0, 1.0 - confidence_variance * 2)
        major_disagreement = confidence_variance > 0.15
        
        best_agent_idx = confidences.index(max(confidences))
        best_agent = agent_results[best_agent_idx]
        
        self.logger.debug(f"Consensus analysis complete - strength: {consensus_strength:.2f}")
        
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
        self.logger.debug("Detecting reasoning forks")
        forks = []
        
        if consensus_analysis["major_disagreement"]:
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
                self.logger.info(f"Detected fork: {fork_info['reason']}")
        
        return forks
    
    def _synthesize_agent_results(
        self, 
        agent_results: List[Dict[str, Any]], 
        consensus_analysis: Dict[str, Any], 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize final research output from agent results"""
        self.logger.debug("Synthesizing agent results")
        
        if not agent_results:
            return {
                "answer": "Unable to conduct research - no agents available",
                "confidence": 0.1,
                "requires_expert_review": True
            }
        
        best_agent = consensus_analysis["best_agent"]
        
        if consensus_analysis["agreement_level"] == "high":
            answer = best_agent["answer"]
            confidence = min(0.99, best_agent["confidence"] * 1.1)
            requires_review = False
        else:
            answer = f"Research indicates: {best_agent['answer']} (Note: Agents showed disagreement)"
            confidence = best_agent["confidence"] * 0.9
            requires_review = True
        
        alternatives = []
        for agent in agent_results:
            if agent["agent_id"] != best_agent["agent_id"] and agent["confidence"] > 0.6:
                alternatives.append({
                    "hypothesis": agent["answer"],
                    "confidence": agent["confidence"],
                    "persona": agent["persona"]
                })
        
        self.logger.debug(f"Synthesis complete with {len(alternatives)} alternatives")
        
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
        self.logger.debug("Calculating research confidence")
        
        if not agent_results:
            return 0.1
        
        base_confidence = consensus_analysis["avg_confidence"]
        
        if consensus_analysis["agreement_level"] == "high":
            base_confidence *= 1.1
            self.logger.debug("Applying high consensus confidence boost")
        elif consensus_analysis["agreement_level"] == "low":
            base_confidence *= 0.8
            self.logger.debug("Applying low consensus confidence penalty")
        
        high_conf_count = sum(1 for r in agent_results if r["confidence"] > 0.8)
        if high_conf_count >= 3:
            base_confidence *= 1.05
            self.logger.debug("Applying multi-agent high confidence boost")
        
        final_confidence = min(1.0, max(0.1, base_confidence))
        self.logger.debug(f"Final research confidence: {final_confidence:.2f}")
        return final_confidence
    
    def _determine_research_strategy(self, complexity: float, knowledge_available: bool, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine research strategy based on input characteristics"""
        strategy = {
            "approach": "comprehensive" if complexity > 0.7 else "focused",
            "agent_count": min(5, max(3, int(complexity * 6))),
            "specialization_needed": complexity > 0.8,
            "evidence_threshold": 0.8 if complexity > 0.6 else 0.7,
            "consensus_required": complexity > 0.5
        }
        
        if not knowledge_available:
            strategy["agent_count"] += 1
            strategy["research_depth"] = "deep"
        else:
            strategy["research_depth"] = "validation"
            
        return strategy
    
    def _calculate_research_metrics(self, agent_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metrics for research quality assessment"""
        if not agent_results:
            return {"quality_score": 0.0, "coverage_score": 0.0, "consensus_score": 0.0}
            
        confidences = [r["confidence"] for r in agent_results]
        avg_confidence = sum(confidences) / len(confidences)
        confidence_variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)
        
        return {
            "quality_score": avg_confidence,
            "coverage_score": min(1.0, len(agent_results) / 5.0),
            "consensus_score": max(0.0, 1.0 - confidence_variance * 2),
            "agent_count": len(agent_results),
            "avg_confidence": avg_confidence,
            "confidence_variance": confidence_variance
        }
