"""
Agent Manager for UKG/USKD Simulation System
Handles agent orchestration, spawning, management, and coordination
"""

import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all simulation agents"""
    
    def __init__(self, agent_id: str, persona: str, role: str, axes: List[float]):
        self.agent_id = agent_id
        self.persona = persona
        self.role = role
        self.axes = axes
        self.created_at = datetime.now()
        self.active = True
        self.context = {}
        self.trace_log = []
        
    @abstractmethod
    def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return agent's response"""
        pass
    
    def log_trace(self, event: str, data: Dict[str, Any]):
        """Log agent activity for tracing"""
        self.trace_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "data": data
        })
    
    def deactivate(self):
        """Deactivate the agent"""
        self.active = False
        self.log_trace("deactivated", {"reason": "manual_deactivation"})


class ResearchAgent(BaseAgent):
    """Research agent for Layer 3+ operations"""
    
    def __init__(self, agent_id: str, persona: str, axes: List[float], specialization: str = "general"):
        super().__init__(agent_id, persona, "researcher", axes)
        self.specialization = specialization
        self.confidence_threshold = 0.8
        
    def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform research analysis"""
        query = input_data.get("query", input_data.get("user_query", ""))
        
        self.log_trace("research_start", {"query": query, "specialization": self.specialization})
        
        # Simulated research process based on persona and specialization
        if self.persona == "domain_expert":
            confidence = 0.9
            reasoning = f"Domain expertise applied to analyze '{query}'"
            answer = f"Expert analysis suggests: {self._generate_expert_response(query)}"
            
        elif self.persona == "critical_thinker":
            confidence = 0.75
            reasoning = f"Critical analysis reveals potential issues with '{query}'"
            answer = f"Critical evaluation indicates: {self._generate_critical_response(query)}"
            
        elif self.persona == "creative_reasoner":
            confidence = 0.7
            reasoning = f"Creative approaches explored for '{query}'"
            answer = f"Alternative perspective: {self._generate_creative_response(query)}"
            
        elif self.persona == "safety_analyst":
            confidence = 0.85
            reasoning = f"Safety assessment conducted for '{query}'"
            answer = f"Safety analysis shows: {self._generate_safety_response(query)}"
            
        else:  # general researcher
            confidence = 0.8
            reasoning = f"General research conducted on '{query}'"
            answer = f"Research indicates: {self._generate_general_response(query)}"
        
        result = {
            "agent_id": self.agent_id,
            "persona": self.persona,
            "answer": answer,
            "confidence": confidence,
            "reasoning": reasoning,
            "specialization": self.specialization
        }
        
        self.log_trace("research_complete", result)
        return result
    
    def _generate_expert_response(self, query: str) -> str:
        return f"Based on domain knowledge, {query.lower()} requires specialized consideration"
    
    def _generate_critical_response(self, query: str) -> str:
        return f"Critical examination of {query.lower()} reveals underlying assumptions that need validation"
    
    def _generate_creative_response(self, query: str) -> str:
        return f"Innovative approach to {query.lower()} suggests alternative methodologies"
    
    def _generate_safety_response(self, query: str) -> str:
        return f"Safety evaluation of {query.lower()} shows acceptable risk with proper precautions"
    
    def _generate_general_response(self, query: str) -> str:
        return f"Analysis of {query.lower()} indicates standard approaches are applicable"


class POVAgent(BaseAgent):
    """Point-of-view agent for Layer 4 perspective analysis"""
    
    def __init__(self, agent_id: str, persona: str, axes: List[float], stakeholder_type: str):
        super().__init__(agent_id, persona, "pov_analyst", axes)
        self.stakeholder_type = stakeholder_type
        
    def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze from specific stakeholder perspective"""
        query = input_data.get("query", "")
        
        self.log_trace("pov_analysis_start", {
            "stakeholder_type": self.stakeholder_type,
            "persona": self.persona
        })
        
        # Generate perspective-specific analysis
        perspective_analysis = self._generate_perspective_analysis(query)
        
        result = {
            "agent_id": self.agent_id,
            "persona": self.persona,
            "stakeholder_type": self.stakeholder_type,
            "perspective_analysis": perspective_analysis,
            "concerns": self._identify_stakeholder_concerns(query),
            "priorities": self._identify_stakeholder_priorities(query),
            "confidence": 0.8
        }
        
        self.log_trace("pov_analysis_complete", result)
        return result
    
    def _generate_perspective_analysis(self, query: str) -> str:
        return f"From {self.stakeholder_type} perspective: {query} impacts..."
    
    def _identify_stakeholder_concerns(self, query: str) -> List[str]:
        concern_map = {
            "users": ["usability", "privacy", "cost"],
            "developers": ["feasibility", "resources", "technical_debt"],
            "regulators": ["compliance", "safety", "fairness"],
            "investors": ["profitability", "risk", "market_impact"]
        }
        return concern_map.get(self.stakeholder_type, ["impact", "risk"])
    
    def _identify_stakeholder_priorities(self, query: str) -> List[str]:
        priority_map = {
            "users": ["value", "ease_of_use", "reliability"],
            "developers": ["maintainability", "performance", "scalability"],
            "regulators": ["public_safety", "fair_competition", "transparency"],
            "investors": ["ROI", "growth_potential", "risk_mitigation"]
        }
        return priority_map.get(self.stakeholder_type, ["benefit", "sustainability"])


class AgentTeam:
    """Manages a team of agents working on the same problem"""
    
    def __init__(self, team_id: str, agents: List[BaseAgent]):
        self.team_id = team_id
        self.agents = agents
        self.created_at = datetime.now()
        
    def process_collaborative(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process input collaboratively across all team agents"""
        results = []
        
        for agent in self.agents:
            if agent.active:
                try:
                    result = agent.process(input_data, context)
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Agent {agent.agent_id} failed: {e}")
        
        # Analyze team consensus
        consensus_analysis = self._analyze_consensus(results)
        
        return {
            "team_id": self.team_id,
            "agent_results": results,
            "consensus_analysis": consensus_analysis,
            "team_confidence": consensus_analysis.get("team_confidence", 0.5)
        }
    
    def _analyze_consensus(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze consensus among agent results"""
        if not results:
            return {"consensus_strength": 0.0, "team_confidence": 0.0}
        
        confidences = [r.get("confidence", 0.5) for r in results]
        avg_confidence = sum(confidences) / len(confidences)
        confidence_variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)
        
        # Simple consensus calculation
        consensus_strength = max(0.0, 1.0 - confidence_variance)
        
        return {
            "consensus_strength": consensus_strength,
            "team_confidence": avg_confidence,
            "agent_count": len(results),
            "confidence_variance": confidence_variance,
            "agreement_level": "high" if consensus_strength > 0.8 else "medium" if consensus_strength > 0.5 else "low"
        }


class AgentManager:
    """
    Central manager for all simulation agents.
    Handles agent lifecycle, coordination, and orchestration.
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.teams: Dict[str, AgentTeam] = {}
        self.agent_personas = [
            "domain_expert", "critical_thinker", "creative_reasoner", 
            "safety_analyst", "synthesizer", "qa_expert"
        ]
        self.pov_stakeholders = [
            "users", "developers", "investors", "regulators", 
            "competitors", "society", "environment"
        ]
        
    def spawn_research_agents(
        self, 
        count: int, 
        axes: List[float], 
        context: Dict[str, Any],
        specializations: Optional[List[str]] = None
    ) -> List[str]:
        """Spawn research agents for Layer 3+ operations"""
        
        agent_ids = []
        specializations = specializations or ["general"] * count
        
        for i in range(count):
            agent_id = f"research_{uuid.uuid4().hex[:8]}"
            persona = self.agent_personas[i % len(self.agent_personas)]
            specialization = specializations[i % len(specializations)]
            
            agent = ResearchAgent(
                agent_id=agent_id,
                persona=persona,
                axes=axes.copy(),
                specialization=specialization
            )
            
            self.agents[agent_id] = agent
            agent_ids.append(agent_id)
            
            logger.info(f"Spawned research agent: {agent_id} ({persona}, {specialization})")
        
        return agent_ids
    
    def spawn_pov_agents(
        self, 
        stakeholder_types: List[str], 
        axes: List[float], 
        context: Dict[str, Any]
    ) -> List[str]:
        """Spawn POV agents for Layer 4 perspective analysis"""
        
        agent_ids = []
        
        for stakeholder_type in stakeholder_types:
            agent_id = f"pov_{stakeholder_type}_{uuid.uuid4().hex[:8]}"
            persona = f"{stakeholder_type}_representative"
            
            agent = POVAgent(
                agent_id=agent_id,
                persona=persona,
                axes=axes.copy(),
                stakeholder_type=stakeholder_type
            )
            
            self.agents[agent_id] = agent
            agent_ids.append(agent_id)
            
            logger.info(f"Spawned POV agent: {agent_id} ({stakeholder_type})")
        
        return agent_ids
    
    def create_agent_team(
        self, 
        agent_ids: List[str], 
        team_name: Optional[str] = None
    ) -> str:
        """Create a team from existing agents"""
        
        team_id = team_name or f"team_{uuid.uuid4().hex[:8]}"
        agents = [self.agents[aid] for aid in agent_ids if aid in self.agents]
        
        team = AgentTeam(team_id, agents)
        self.teams[team_id] = team
        
        logger.info(f"Created agent team: {team_id} with {len(agents)} agents")
        return team_id
    
    def run_agent_team(
        self, 
        team_id: str, 
        input_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run collaborative processing on an agent team"""
        
        team = self.teams.get(team_id)
        if not team:
            raise ValueError(f"Team {team_id} not found")
        
        return team.process_collaborative(input_data, context)
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def deactivate_agent(self, agent_id: str) -> bool:
        """Deactivate an agent"""
        agent = self.agents.get(agent_id)
        if agent:
            agent.deactivate()
            return True
        return False
    
    def get_active_agents(self) -> List[BaseAgent]:
        """Get all active agents"""
        return [agent for agent in self.agents.values() if agent.active]
    
    def get_agent_traces(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get trace log for a specific agent"""
        agent = self.agents.get(agent_id)
        return agent.trace_log if agent else []
    
    def cleanup_inactive_agents(self):
        """Remove inactive agents from memory"""
        active_agents = {aid: agent for aid, agent in self.agents.items() if agent.active}
        removed_count = len(self.agents) - len(active_agents)
        self.agents = active_agents
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} inactive agents")
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get statistics about current agents"""
        active_count = len(self.get_active_agents())
        total_count = len(self.agents)
        
        persona_counts = {}
        for agent in self.agents.values():
            persona_counts[agent.persona] = persona_counts.get(agent.persona, 0) + 1
        
        return {
            "total_agents": total_count,
            "active_agents": active_count,
            "inactive_agents": total_count - active_count,
            "teams": len(self.teams),
            "persona_distribution": persona_counts
        }
