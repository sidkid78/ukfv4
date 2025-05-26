"""
Layer 4: Point-of-View (POV) Engine
Handles perspective triangulation, stakeholder analysis, and multi-viewpoint reasoning
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

from .base import BaseLayer, LayerResult, register_layer
from core.memory import InMemoryKnowledgeGraph


@register_layer(4)
class Layer4POVEngine(BaseLayer):
    """
    Point-of-View Engine for perspective triangulation and stakeholder analysis.
    Examines issues from multiple viewpoints to identify biases and blind spots.
    """
    
    def __init__(self):
        super().__init__()
        self.layer_number = 4
        self.layer_name = "Point-of-View (POV) Engine"
        self.confidence_threshold = 0.99
        self.requires_agents = True
        self.requires_memory = True
        
    def process(
        self, 
        input_data: Dict[str, Any], 
        state: Dict[str, Any], 
        memory: InMemoryKnowledgeGraph,
        agents: Optional[List[Any]] = None
    ) -> LayerResult:
        """Process multi-perspective analysis and viewpoint triangulation"""
        
        query = input_data.get("normalized_query", input_data.get("query", ""))
        query_type = input_data.get("query_type", "general")
        research_answer = input_data.get("research_answer")
        
        # Identify relevant stakeholders and perspectives
        stakeholder_analysis = self._identify_stakeholders(query, query_type)
        
        # Generate perspective-specific analyses
        pov_analyses = self._generate_pov_analyses(
            query, research_answer, stakeholder_analysis, memory
        )
        
        # Perform triangulation to find convergent insights
        triangulation_results = self._triangulate_perspectives(pov_analyses)
        
        # Identify biases and blind spots
        bias_analysis = self._analyze_biases_and_blindspots(pov_analyses, triangulation_results)
        
        # Detect perspective conflicts that may require forking
        perspective_conflicts = self._detect_perspective_conflicts(pov_analyses)
        
        # Generate comprehensive multi-perspective synthesis
        pov_synthesis = self._synthesize_perspectives(
            pov_analyses, triangulation_results, bias_analysis
        )
        
        # Calculate confidence based on perspective convergence
        confidence = self._calculate_pov_confidence(
            triangulation_results, bias_analysis, pov_synthesis
        )
        
        # Determine escalation need
        escalate = (
            self.should_escalate(confidence) or
            bias_analysis.get("high_bias_risk", False) or
            len(perspective_conflicts) > 2
        )
        
        output = {
            **input_data,
            "pov_analysis_conducted": True,
            "stakeholder_analysis": stakeholder_analysis,
            "perspective_analyses": pov_analyses,
            "triangulation_results": triangulation_results,
            "bias_analysis": bias_analysis,
            "pov_synthesis": pov_synthesis,
            "perspective_conflicts": perspective_conflicts,
            "multi_perspective_answer": pov_synthesis.get("answer"),
            "perspective_confidence": pov_synthesis.get("confidence")
        }
        
        trace = {
            "stakeholders_identified": len(stakeholder_analysis["stakeholders"]),
            "perspectives_analyzed": len(pov_analyses),
            "convergent_insights": len(triangulation_results.get("convergent_points", [])),
            "bias_concerns": len(bias_analysis.get("identified_biases", [])),
            "perspective_conflicts": len(perspective_conflicts),
            "persona_reasonings": {
                analysis["perspective"]: analysis["reasoning"]
                for analysis in pov_analyses
            }
        }
        
        forks = []
        if perspective_conflicts:
            forks = self._create_perspective_forks(perspective_conflicts)
        
        return LayerResult(
            output=output,
            confidence=confidence,
            escalate=escalate,
            trace=trace,
            forks=forks,
            metadata={"pov_layer": True, "perspectives_count": len(pov_analyses)}
        )
    
    def _identify_stakeholders(self, query: str, query_type: str) -> Dict[str, Any]:
        """Identify relevant stakeholders and their perspectives"""
        
        # Base stakeholder categories
        stakeholder_categories = {
            "primary": [],    # Directly affected
            "secondary": [],  # Indirectly affected
            "regulatory": [], # Oversight/governance
            "expert": [],     # Domain expertise
            "public": []      # General public interest
        }
        
        # Determine stakeholders based on query type and content
        query_lower = query.lower()
        
        # Technology/AI related stakeholders
        if any(term in query_lower for term in ["ai", "technology", "algorithm", "automation"]):
            stakeholder_categories["primary"].extend(["developers", "users", "businesses"])
            stakeholder_categories["secondary"].extend(["workers", "consumers"])
            stakeholder_categories["regulatory"].extend(["tech_regulators", "ethics_boards"])
            stakeholder_categories["expert"].extend(["ai_researchers", "ethicists"])
            stakeholder_categories["public"].append("general_public")
        
        # Healthcare related stakeholders
        if any(term in query_lower for term in ["health", "medical", "patient", "treatment"]):
            stakeholder_categories["primary"].extend(["patients", "doctors", "nurses"])
            stakeholder_categories["secondary"].extend(["families", "insurance"])
            stakeholder_categories["regulatory"].extend(["health_regulators", "medical_boards"])
            stakeholder_categories["expert"].extend(["medical_experts", "researchers"])
        
        # Environmental stakeholders
        if any(term in query_lower for term in ["environment", "climate", "pollution", "sustainability"]):
            stakeholder_categories["primary"].extend(["communities", "future_generations"])
            stakeholder_categories["secondary"].extend(["businesses", "governments"])
            stakeholder_categories["regulatory"].extend(["environmental_agencies"])
            stakeholder_categories["expert"].extend(["environmental_scientists", "activists"])
        
        # Economic stakeholders
        if any(term in query_lower for term in ["economic", "financial", "market", "business"]):
            stakeholder_categories["primary"].extend(["investors", "businesses", "consumers"])
            stakeholder_categories["secondary"].extend(["workers", "communities"])
            stakeholder_categories["regulatory"].extend(["financial_regulators", "central_banks"])
            stakeholder_categories["expert"].extend(["economists", "analysts"])
        
        # Remove duplicates and ensure we have stakeholders
        for category in stakeholder_categories:
            stakeholder_categories[category] = list(set(stakeholder_categories[category]))
        
        # If no specific stakeholders identified, use general ones
        if not any(stakeholder_categories.values()):
            stakeholder_categories["primary"] = ["affected_parties"]
            stakeholder_categories["expert"] = ["domain_experts"]
            stakeholder_categories["public"] = ["general_public"]
        
        return {
            "stakeholders": stakeholder_categories,
            "total_count": sum(len(cats) for cats in stakeholder_categories.values()),
            "analysis_scope": "comprehensive" if sum(len(cats) for cats in stakeholder_categories.values()) > 8 else "focused"
        }
    
    def _generate_pov_analyses(
        self, 
        query: str, 
        research_answer: str, 
        stakeholder_analysis: Dict[str, Any], 
        memory: InMemoryKnowledgeGraph
    ) -> List[Dict[str, Any]]:
        """Generate analysis from each identified perspective"""
        
        analyses = []
        stakeholders = stakeholder_analysis["stakeholders"]
        
        # Generate analysis for each stakeholder category
        for category, stakeholder_list in stakeholders.items():
            for stakeholder in stakeholder_list[:2]:  # Limit to 2 per category for performance
                analysis = self._simulate_stakeholder_perspective(
                    stakeholder, category, query, research_answer, memory
                )
                analyses.append(analysis)
        
        return analyses
    
    def _simulate_stakeholder_perspective(
        self, 
        stakeholder: str, 
        category: str, 
        query: str, 
        research_answer: str, 
        memory: InMemoryKnowledgeGraph
    ) -> Dict[str, Any]:
        """Simulate analysis from a specific stakeholder perspective"""
        
        perspective_id = f"{category}_{stakeholder}"
        
        # Stakeholder-specific concerns and priorities
        concerns = self._get_stakeholder_concerns(stakeholder, category)
        priorities = self._get_stakeholder_priorities(stakeholder, category)
        
        # Generate perspective-specific response
        if research_answer:
            perspective_response = f"From {stakeholder} perspective: {research_answer}"
            base_confidence = 0.8
            
            # Adjust based on stakeholder alignment
            if category == "expert":
                base_confidence += 0.1
            elif category == "regulatory":
                base_confidence += 0.05
            
        else:
            perspective_response = f"{stakeholder} perspective on '{query}' requires consideration of {', '.join(concerns[:2])}"
            base_confidence = 0.6
        
        reasoning = f"Analysis prioritizes {', '.join(priorities[:2])} while addressing {', '.join(concerns[:2])}"
        
        return {
            "perspective": perspective_id,
            "stakeholder": stakeholder,
            "category": category,
            "response": perspective_response,
            "confidence": min(0.95, base_confidence),
            "concerns": concerns,
            "priorities": priorities,
            "reasoning": reasoning,
            "bias_indicators": self._identify_perspective_biases(stakeholder, category)
        }
    
    def _get_stakeholder_concerns(self, stakeholder: str, category: str) -> List[str]:
        """Get typical concerns for a stakeholder type"""
        
        concern_mapping = {
            "developers": ["feasibility", "technical_constraints", "resource_requirements"],
            "users": ["usability", "privacy", "safety", "cost"],
            "businesses": ["profitability", "market_impact", "competitive_advantage"],
            "workers": ["job_security", "workplace_safety", "fair_compensation"],
            "patients": ["safety", "efficacy", "accessibility", "side_effects"],
            "doctors": ["clinical_effectiveness", "patient_safety", "workflow_impact"],
            "communities": ["local_impact", "environmental_effects", "social_equity"],
            "investors": ["returns", "risk_management", "market_stability"],
            "regulators": ["compliance", "public_safety", "market_fairness"],
            "general_public": ["safety", "fairness", "transparency", "social_impact"]
        }
        
        return concern_mapping.get(stakeholder, ["impact", "fairness", "safety"])
    
    def _get_stakeholder_priorities(self, stakeholder: str, category: str) -> List[str]:
        """Get typical priorities for a stakeholder type"""
        
        priority_mapping = {
            "developers": ["innovation", "technical_excellence", "efficiency"],
            "users": ["ease_of_use", "value", "reliability"],
            "businesses": ["growth", "sustainability", "competitiveness"],
            "workers": ["job_stability", "skill_development", "working_conditions"],
            "patients": ["health_outcomes", "quality_of_life", "affordability"],
            "doctors": ["patient_care", "evidence_based_practice", "efficiency"],
            "communities": ["well_being", "sustainability", "inclusion"],
            "investors": ["profit_maximization", "risk_minimization", "growth"],
            "regulators": ["public_protection", "market_stability", "compliance"],
            "general_public": ["collective_benefit", "transparency", "fairness"]
        }
        
        return priority_mapping.get(stakeholder, ["benefit", "safety", "fairness"])
    
    def _identify_perspective_biases(self, stakeholder: str, category: str) -> List[str]:
        """Identify potential biases for this perspective"""
        
        bias_mapping = {
            "developers": ["technical_optimism", "complexity_underestimation"],
            "businesses": ["profit_focus", "short_term_thinking"],
            "regulators": ["risk_aversion", "status_quo_bias"],
            "experts": ["confirmation_bias", "overconfidence"],
            "users": ["availability_bias", "present_bias"],
            "investors": ["herding_behavior", "loss_aversion"]
        }
        
        category_biases = {
            "primary": ["self_interest"],
            "secondary": ["distance_bias"],
            "regulatory": ["bureaucratic_inertia"],
            "expert": ["expert_bias"],
            "public": ["availability_heuristic"]
        }
        
        biases = bias_mapping.get(stakeholder, []) + category_biases.get(category, [])
        return list(set(biases))
    
    def _triangulate_perspectives(self, pov_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find convergent insights across different perspectives"""
        
        # Extract common themes and concerns
        all_concerns = []
        all_priorities = []
        responses = []
        
        for analysis in pov_analyses:
            all_concerns.extend(analysis.get("concerns", []))
            all_priorities.extend(analysis.get("priorities", []))
            responses.append(analysis.get("response", ""))
        
        # Find convergent points
        concern_frequency = {}
        for concern in all_concerns:
            concern_frequency[concern] = concern_frequency.get(concern, 0) + 1
        
        priority_frequency = {}
        for priority in all_priorities:
            priority_frequency[priority] = priority_frequency.get(priority, 0) + 1
        
        # Identify convergent themes (mentioned by multiple perspectives)
        convergent_concerns = [
            concern for concern, freq in concern_frequency.items() 
            if freq >= 2
        ]
        
        convergent_priorities = [
            priority for priority, freq in priority_frequency.items() 
            if freq >= 2
        ]
        
        # Calculate convergence strength
        total_perspectives = len(pov_analyses)
        convergence_strength = (
            len(convergent_concerns) + len(convergent_priorities)
        ) / max(1, total_perspectives * 2)
        
        return {
            "convergent_concerns": convergent_concerns,
            "convergent_priorities": convergent_priorities,
            "convergence_strength": min(1.0, convergence_strength),
            "consensus_areas": self._identify_consensus_areas(responses),
            "divergent_areas": self._identify_divergent_areas(pov_analyses)
        }
    
    def _identify_consensus_areas(self, responses: List[str]) -> List[str]:
        """Identify areas where perspectives agree"""
        # Simplified consensus detection
        consensus_areas = ["safety", "effectiveness", "fairness"]
        return consensus_areas
    
    def _identify_divergent_areas(self, pov_analyses: List[Dict[str, Any]]) -> List[str]:
        """Identify areas where perspectives significantly differ"""
        # Simplified divergence detection
        divergent_areas = []
        
        confidences = [analysis.get("confidence", 0.5) for analysis in pov_analyses]
        if max(confidences) - min(confidences) > 0.3:
            divergent_areas.append("confidence_levels")
        
        # Check for conflicting priorities
        all_priorities = []
        for analysis in pov_analyses:
            all_priorities.extend(analysis.get("priorities", []))
        
        conflicting_pairs = [
            ("profit_maximization", "cost_minimization"),
            ("innovation", "safety"),
            ("efficiency", "thoroughness")
        ]
        
        for priority1, priority2 in conflicting_pairs:
            if priority1 in all_priorities and priority2 in all_priorities:
                divergent_areas.append(f"{priority1}_vs_{priority2}")
        
        return divergent_areas
    
    def _analyze_biases_and_blindspots(
        self, 
        pov_analyses: List[Dict[str, Any]], 
        triangulation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze potential biases and blind spots in the perspective analysis"""
        
        # Collect all identified biases
        all_biases = []
        for analysis in pov_analyses:
            all_biases.extend(analysis.get("bias_indicators", []))
        
        bias_frequency = {}
        for bias in all_biases:
            bias_frequency[bias] = bias_frequency.get(bias, 0) + 1
        
        # Identify high-risk biases (appearing frequently)
        high_risk_biases = [
            bias for bias, freq in bias_frequency.items() 
            if freq >= len(pov_analyses) * 0.3
        ]
        
        # Identify potential blind spots
        blind_spots = self._identify_blind_spots(pov_analyses)
        
        # Assess overall bias risk
        bias_risk_level = "high" if len(high_risk_biases) > 2 else "medium" if high_risk_biases else "low"
        
        return {
            "identified_biases": list(bias_frequency.keys()),
            "high_risk_biases": high_risk_biases,
            "bias_frequency": bias_frequency,
            "blind_spots": blind_spots,
            "bias_risk_level": bias_risk_level,
            "high_bias_risk": bias_risk_level == "high",
            "mitigation_needed": len(high_risk_biases) > 1 or len(blind_spots) > 2
        }
    
    def _identify_blind_spots(self, pov_analyses: List[Dict[str, Any]]) -> List[str]:
        """Identify potential blind spots not covered by any perspective"""
        
        # Common blind spots to check for
        potential_blind_spots = [
            "long_term_consequences",
            "unintended_effects",
            "minority_perspectives",
            "international_implications",
            "technical_limitations",
            "ethical_implications",
            "environmental_impact",
            "social_equity"
        ]
        
        # Check which concerns are covered
        covered_concerns = set()
        for analysis in pov_analyses:
            covered_concerns.update(analysis.get("concerns", []))
        
        # Identify uncovered areas
        blind_spots = []
        for blind_spot in potential_blind_spots:
            if not any(concern in blind_spot or blind_spot in concern 
                      for concern in covered_concerns):
                blind_spots.append(blind_spot)
        
        return blind_spots
    
    def _detect_perspective_conflicts(self, pov_analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect significant conflicts between perspectives"""
        
        conflicts = []
        
        # Compare perspectives pairwise
        for i, analysis1 in enumerate(pov_analyses):
            for j, analysis2 in enumerate(pov_analyses[i+1:], i+1):
                conflict = self._assess_perspective_conflict(analysis1, analysis2)
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    def _assess_perspective_conflict(
        self, 
        analysis1: Dict[str, Any], 
        analysis2: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Assess if two perspectives are in significant conflict"""
        
        # Check confidence difference
        conf_diff = abs(analysis1.get("confidence", 0.5) - analysis2.get("confidence", 0.5))
        
        # Check priority conflicts
        priorities1 = set(analysis1.get("priorities", []))
        priorities2 = set(analysis2.get("priorities", []))
        
        conflicting_priorities = [
            ("profit_maximization", "cost_reduction"),
            ("speed", "safety"),
            ("innovation", "stability")
        ]
        
        has_priority_conflict = any(
            p1 in priorities1 and p2 in priorities2 
            for p1, p2 in conflicting_priorities
        )
        
        if conf_diff > 0.25 or has_priority_conflict:
            return {
                "id": str(uuid.uuid4()),
                "perspective1": analysis1.get("perspective"),
                "perspective2": analysis2.get("perspective"),
                "conflict_type": "priority_conflict" if has_priority_conflict else "confidence_conflict",
                "confidence_difference": conf_diff,
                "priority_conflict": has_priority_conflict,
                "severity": "high" if (conf_diff > 0.4 or has_priority_conflict) else "medium"
            }
        
        return None
    
    def _create_perspective_forks(self, conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create forks for significant perspective conflicts"""
        
        forks = []
        
        for conflict in conflicts:
            if conflict.get("severity") == "high":
                fork = {
                    "id": str(uuid.uuid4()),
                    "layer": self.layer_number,
                    "type": "perspective_conflict",
                    "conflict_id": conflict["id"],
                    "perspectives": [conflict["perspective1"], conflict["perspective2"]],
                    "conflict_type": conflict["conflict_type"],
                    "reason": f"Significant {conflict['conflict_type']} between {conflict['perspective1']} and {conflict['perspective2']}",
                    "requires_mediation": True
                }
                forks.append(fork)
        
        return forks
    
    def _synthesize_perspectives(
        self, 
        pov_analyses: List[Dict[str, Any]], 
        triangulation_results: Dict[str, Any], 
        bias_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize insights from all perspectives into coherent analysis"""
        
        if not pov_analyses:
            return {
                "answer": "Unable to conduct perspective analysis",
                "confidence": 0.1
            }
        
        # Weight perspectives by category and confidence
        weighted_responses = []
        total_weight = 0
        
        for analysis in pov_analyses:
            # Weight by category importance and confidence
            category = analysis.get("category", "primary")
            confidence = analysis.get("confidence", 0.5)
            
            category_weight = {
                "expert": 1.2,
                "primary": 1.0,
                "regulatory": 1.1,
                "secondary": 0.8,
                "public": 0.9
            }.get(category, 1.0)
            
            weight = category_weight * confidence
            weighted_responses.append({
                "response": analysis.get("response", ""),
                "weight": weight,
                "perspective": analysis.get("perspective", "")
            })
            total_weight += weight
        
        # Create synthesis based on convergent insights
        convergent_concerns = triangulation_results.get("convergent_concerns", [])
        convergent_priorities = triangulation_results.get("convergent_priorities", [])
        # Generate synthesized answer
        if triangulation_results.get("convergence_strength", 0) > 0.7:
            synthesis_answer = f"Multi-perspective analysis reveals strong convergence around {', '.join(convergent_concerns[:3])}"
            synthesis_confidence = min(0.95, triangulation_results["convergence_strength"] * 1.1)
        else:
            # Find the highest weighted response
            best_response = max(weighted_responses, key=lambda x: x["weight"])
            synthesis_answer = f"Perspective analysis suggests: {best_response['response']} (Note: Limited convergence across viewpoints)"
            synthesis_confidence = best_response["weight"] / max(total_weight / len(weighted_responses), 1.0)
            synthesis_confidence = min(0.9, synthesis_confidence)
        
        # Apply bias adjustment
        if bias_analysis.get("high_bias_risk", False):
            synthesis_confidence *= 0.85
        
        return {
            "answer": synthesis_answer,
            "confidence": max(0.1, synthesis_confidence),
            "convergent_insights": convergent_concerns + convergent_priorities,
            "perspective_weights": {r["perspective"]: r["weight"] for r in weighted_responses},
            "bias_adjusted": bias_analysis.get("high_bias_risk", False),
            "synthesis_quality": "high" if triangulation_results.get("convergence_strength", 0) > 0.7 else "medium"
        }
    
    def _calculate_pov_confidence(
        self, 
        triangulation_results: Dict[str, Any], 
        bias_analysis: Dict[str, Any], 
        pov_synthesis: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence for POV analysis"""
        
        base_confidence = pov_synthesis.get("confidence", 0.5)
        
        # Boost for strong convergence
        convergence_strength = triangulation_results.get("convergence_strength", 0)
        base_confidence += convergence_strength * 0.2
        
        # Penalty for high bias risk
        if bias_analysis.get("high_bias_risk", False):
            base_confidence *= 0.8
        
        # Penalty for many blind spots
        blind_spot_count = len(bias_analysis.get("blind_spots", []))
        if blind_spot_count > 3:
            base_confidence *= 0.9
        
        return min(1.0, max(0.1, base_confidence))
        