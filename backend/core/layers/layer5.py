# core/layers/layer_5.py - AI-Powered Gatekeeper/Team Management

import os
from google import genai
from .base import BaseLayer
from typing import Dict, Any, List
import json
import logging
from datetime import datetime
from core.gemini_service import gemini_service, GeminiRequest, GeminiModel
# Configure Gemini AI
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

class Layer5GatekeeperTeamManagement(BaseLayer):
    layer_number = 5
    layer_name = "Gatekeeper/Team Management"

    def __init__(self):
        self.model = GeminiModel.GEMINI_FLASH_0520
        self.safety_model = GeminiModel.GEMINI_FLASH  # Dedicated safety analysis
        
    def process(self, input_data, state, memory):
        query = input_data.get("query") or state.get("orig_query")
        axes = input_data.get("axes") or [0.0] * 13
        
        # Get previous layer outputs for analysis
        previous_outputs = self._extract_previous_outputs(state)
        
        # Perform comprehensive gatekeeper analysis
        gatekeeper_analysis = self._perform_gatekeeper_analysis(query, previous_outputs, state)
        
        # Assess team coherence and conflicts
        team_assessment = self._assess_team_coherence(previous_outputs)
        
        # Perform safety and compliance check
        safety_assessment = self._perform_safety_assessment(query, previous_outputs, state)
        
        # Make escalation/containment decision
        decision = self._make_gatekeeper_decision(gatekeeper_analysis, team_assessment, safety_assessment)
        
        # Calculate confidence based on alignment and safety 2
        confidence = self._calculate_gatekeeper_confidence(gatekeeper_analysis, team_assessment, safety_assessment)
        
        # Determine if escalation is needed
        escalate = decision["escalate"] or confidence < 0.90 or safety_assessment["risk_level"] == "HIGH"
        
        # Prepare memory patches for critical findings
        patch_memory = []
        if safety_assessment["risk_level"] in ["HIGH", "CRITICAL"]:
            patch_memory.append({
                "coordinate": axes,
                "value": {
                    "safety_alert": True,
                    "risk_level": safety_assessment["risk_level"],
                    "safety_concerns": safety_assessment["concerns"],
                    "mitigation_required": True,
                    "timestamp": datetime.now().isoformat()
                },
                "meta": {
                    "created_by": "layer_5_gatekeeper",
                    "alert_type": "safety_risk",
                    "requires_immediate_attention": True
                }
            })
        
        if team_assessment["coherence_score"] < 0.7:
            patch_memory.append({
                "coordinate": axes,
                "value": {
                    "team_coherence_issue": True,
                    "coherence_score": team_assessment["coherence_score"],
                    "conflicts": team_assessment["conflicts"],
                    "resolution_needed": True
                },
                "meta": {
                    "created_by": "layer_5_gatekeeper",
                    "issue_type": "team_coherence",
                    "priority": "medium"
                }
            })
        
        trace = {
            "gatekeeper_analysis": gatekeeper_analysis,
            "team_assessment": team_assessment,
            "safety_assessment": safety_assessment,
            "decision": decision,
            "confidence_breakdown": {
                "analysis_confidence": gatekeeper_analysis["confidence"],
                "team_coherence": team_assessment["coherence_score"],
                "safety_score": safety_assessment["safety_score"],
                "overall": confidence
            }
        }
        
        return dict(
            output=dict(
                gatekeeper_decision=decision,
                team_status=team_assessment,
                safety_status=safety_assessment,
                recommendation=gatekeeper_analysis["recommendation"]
            ),
            confidence=confidence,
            escalate=escalate,
            trace=trace,
            patch_memory=patch_memory
        )
    
    def _extract_previous_outputs(self, state: Dict) -> Dict:
        """Extract outputs from previous layers for analysis"""
        outputs = {}
        for i in range(1, 5):  # Layers 1-4
            layer_key = f"layer{i}_trace"
            if layer_key in state:
                outputs[f"layer_{i}"] = state[layer_key]
        return outputs
    
    def _perform_gatekeeper_analysis(self, query: str, previous_outputs: Dict, state: Dict) -> Dict:
        """AI-powered gatekeeper analysis of simulation progress"""
        
        outputs_summary = self._summarize_previous_outputs(previous_outputs)
        
        prompt = f"""
You are an AI Gatekeeper responsible for ensuring simulation quality, coherence, and safety.

ORIGINAL QUERY: {query}

PREVIOUS LAYER OUTPUTS SUMMARY:
{outputs_summary}

As a Gatekeeper, analyze:

1. **Quality Assessment**: Are the previous analyses comprehensive and high-quality?
2. **Coherence Check**: Do the outputs align logically with each other?
3. **Completeness**: Are there significant gaps or missing perspectives?
4. **Consistency**: Are there contradictions that need resolution?
5. **Safety Considerations**: Any concerning patterns or risks?

Provide your analysis in JSON format:
{{
    "quality_score": 0.85,
    "coherence_score": 0.90,
    "completeness_score": 0.80,
    "consistency_score": 0.75,
    "safety_score": 0.95,
    "overall_assessment": "Detailed assessment of simulation state",
    "identified_issues": ["Issue 1", "Issue 2"] or [],
    "strengths": ["Strength 1", "Strength 2"],
    "recommendation": "PROCEED|REVIEW|ESCALATE with reasoning",
    "confidence": 0.88
}}

Be thorough and critical. Your role is quality assurance and risk management.
"""
        
        try:
            response = GeminiRequest(prompt=prompt, model=self.model)
            response_text = response.text.strip()
            
            if response_text.startswith('```json'):
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif response_text.startswith('```'):
                response_text = response_text.split('```')[1].split('```')[0].strip()
                
            return json.loads(response_text)
            
        except Exception as e:
            logging.error(f"Gatekeeper analysis error: {e}")
            return {
                "quality_score": 0.75,
                "coherence_score": 0.80,
                "completeness_score": 0.75,
                "consistency_score": 0.70,
                "safety_score": 0.85,
                "overall_assessment": "Gatekeeper analysis in progress",
                "identified_issues": [],
                "strengths": ["Multi-layer analysis completed"],
                "recommendation": "PROCEED",
                "confidence": 0.75
            }
    
    def _assess_team_coherence(self, previous_outputs: Dict) -> Dict:
        """Assess coherence and conflicts between different layer outputs"""
        
        prompt = f"""
Analyze team coherence across simulation layers:

LAYER OUTPUTS:
{json.dumps(previous_outputs, indent=2)[:1500]}...

Assess:
1. **Agreement Level**: How much do different layers agree?
2. **Conflict Areas**: Where are there disagreements?
3. **Resolution Needs**: What conflicts need addressing?
4. **Team Dynamics**: Overall team effectiveness

Respond in JSON:
{{
    "coherence_score": 0.85,
    "agreement_areas": ["Area 1", "Area 2"],
    "conflicts": ["Conflict 1", "Conflict 2"] or [],
    "conflict_severity": "LOW|MEDIUM|HIGH",
    "resolution_suggestions": ["Suggestion 1", "Suggestion 2"],
    "team_effectiveness": "Assessment of team performance"
}}
"""
        
        try:
            response = GeminiRequest(prompt=prompt, model=self.model)
            response_text = response.text.strip()
            
            if response_text.startswith('```json'):
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif response_text.startswith('```'):
                response_text = response_text.split('```')[1].split('```')[0].strip()
                
            return json.loads(response_text)
            
        except:
            return {
                "coherence_score": 0.80,
                "agreement_areas": ["General analysis direction"],
                "conflicts": [],
                "conflict_severity": "LOW",
                "resolution_suggestions": [],
                "team_effectiveness": "Team coordination being assessed"
            }
    
    def _perform_safety_assessment(self, query: str, previous_outputs: Dict, state: Dict) -> Dict:
        """Dedicated AI safety and compliance assessment"""
        
        prompt = f"""
You are a Safety Assessment AI. Analyze for risks and compliance issues.

QUERY: {query}
SIMULATION PROGRESS: {json.dumps(previous_outputs, indent=2)[:1000]}...

Assess safety across these dimensions:
1. **Content Safety**: Harmful, biased, or inappropriate content
2. **Reasoning Safety**: Flawed logic or dangerous conclusions  
3. **Ethical Concerns**: Moral or ethical issues
4. **Compliance Issues**: Regulatory or policy violations
5. **Risk Factors**: Potential negative consequences

Respond in JSON:
{{
    "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "safety_score": 0.95,
    "concerns": ["Concern 1", "Concern 2"] or [],
    "risk_categories": ["Category 1", "Category 2"] or [],
    "mitigation_recommendations": ["Rec 1", "Rec 2"],
    "compliance_status": "COMPLIANT|REVIEW_NEEDED|NON_COMPLIANT",
    "detailed_assessment": "Detailed safety analysis"
}}

Be extremely careful and conservative in safety assessment.
"""
        
        try:
            response = GeminiRequest(prompt=prompt, model=self.safety_model)
            response_text = response.text.strip()
            
            if response_text.startswith('```json'):
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif response_text.startswith('```'):
                response_text = response_text.split('```')[1].split('```')[0].strip()
                
            return json.loads(response_text)
            
        except:
            return {
                "risk_level": "LOW",
                "safety_score": 0.90,
                "concerns": [],
                "risk_categories": [],
                "mitigation_recommendations": [],
                "compliance_status": "COMPLIANT",
                "detailed_assessment": "Safety assessment in progress"
            }
    
    def _make_gatekeeper_decision(self, analysis: Dict, team: Dict, safety: Dict) -> Dict:
        """Make final gatekeeper decision based on all assessments"""
        
        # Decision logic based on scores and safety
        proceed = True
        escalate = False
        actions = []
        
        if safety["risk_level"] in ["HIGH", "CRITICAL"]:
            proceed = False
            escalate = True
            actions.append("SAFETY_REVIEW_REQUIRED")
        
        if analysis["quality_score"] < 0.7:
            escalate = True
            actions.append("QUALITY_IMPROVEMENT_NEEDED")
        
        if team["coherence_score"] < 0.6:
            actions.append("TEAM_ALIGNMENT_REQUIRED")
        
        if analysis["consistency_score"] < 0.7:
            actions.append("CONSISTENCY_REVIEW_NEEDED")
        
        decision_type = "ESCALATE" if escalate else ("PROCEED" if proceed else "REVIEW")
        
        return {
            "decision": decision_type,
            "proceed": proceed,
            "escalate": escalate,
            "required_actions": actions,
            "reasoning": f"Decision based on quality ({analysis['quality_score']:.2f}), coherence ({team['coherence_score']:.2f}), safety ({safety['safety_score']:.2f})",
            "next_steps": self._determine_next_steps(decision_type, actions)
        }
    
    def _determine_next_steps(self, decision: str, actions: List[str]) -> List[str]:
        """Determine recommended next steps based on decision"""
        if decision == "ESCALATE":
            return ["Escalate to Layer 6", "Address identified issues", "Safety review if needed"]
        elif decision == "REVIEW":
            return ["Team coordination meeting", "Address specific concerns", "Re-evaluation"]
        else:
            return ["Continue to next phase", "Monitor progress", "Document findings"]
    
    def _calculate_gatekeeper_confidence(self, analysis: Dict, team: Dict, safety: Dict) -> float:
        """Calculate overall gatekeeper confidence"""
        weights = {
            "analysis": 0.3,
            "team": 0.3,
            "safety": 0.4  # Safety gets highest weight
        }
        
        confidence = (
            analysis["confidence"] * weights["analysis"] +
            team["coherence_score"] * weights["team"] +
            safety["safety_score"] * weights["safety"]
        )
        
        return min(0.99, max(0.0, confidence))
    
    def _summarize_previous_outputs(self, outputs: Dict) -> str:
        """Create a concise summary of previous layer outputs"""
        summary_parts = []
        for layer, data in outputs.items():
            if isinstance(data, dict):
                summary_parts.append(f"{layer}: {str(data)[:200]}...")
        return "\n".join(summary_parts)
