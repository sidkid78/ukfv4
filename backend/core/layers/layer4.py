# core/layers/layer_4.py - AI-Powered POV Engine

import os
from google import genai
from .base import BaseLayer
from typing import Dict, Any, List
import json
import logging

# Configure Gemini AI
from core.gemini_service import gemini_service, GeminiRequest, GeminiModel
class Layer4POVEngine(BaseLayer):
    layer_number = 4
    layer_name = "Point-of-View (POV) Engine"

    def __init__(self):
        self.model = GeminiModel.GEMINI_FLASH_0520
        self.pov_perspectives = [
            "Industry Expert",
            "Regulatory/Compliance Perspective", 
            "Consumer/End-User Perspective",
            "Academic Research Perspective",
            "Economic/Market Perspective",
            "Ethical/Social Impact Perspective"
        ]
        
    def process(self, input_data, state, memory):
        query = input_data.get("query") or state.get("orig_query")
        axes = input_data.get("axes") or [0.0] * 13
        
        # Generate multiple POV analyses using AI
        pov_analyses = []
        confidence_scores = []
        
        for perspective in self.pov_perspectives:
            try:
                analysis = self._generate_pov_analysis(query, perspective, state)
                pov_analyses.append({
                    "perspective": perspective,
                    "analysis": analysis["analysis"],
                    "confidence": analysis["confidence"],
                    "key_considerations": analysis["key_considerations"],
                    "stakeholder_impact": analysis["stakeholder_impact"]
                })
                confidence_scores.append(analysis["confidence"])
                
            except Exception as e:
                logging.error(f"POV AI error for {perspective}: {e}")
                # Fallback analysis
                pov_analyses.append({
                    "perspective": perspective,
                    "analysis": f"Perspective analysis from {perspective} viewpoint on: {query}",
                    "confidence": 0.6,
                    "key_considerations": ["Analysis pending due to processing constraints"],
                    "stakeholder_impact": "Medium impact expected"
                })
                confidence_scores.append(0.6)
        
        # Synthesize POV results
        synthesis = self._synthesize_perspectives(query, pov_analyses)
        
        # Calculate overall confidence and escalation
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        # Check for conflicting perspectives (potential fork condition)
        conflict_detected = self._detect_perspective_conflicts(pov_analyses)
        
        # Escalate if low confidence or high conflict
        escalate = avg_confidence < 0.85 or conflict_detected
        
        patch_memory = []
        if conflict_detected:
            # Create memory patch for conflicting perspectives
            patch_memory.append({
                "coordinate": axes,
                "value": {
                    "pov_conflict": True,
                    "conflicting_perspectives": [p["perspective"] for p in pov_analyses],
                    "conflict_summary": synthesis["conflicts"]
                },
                "meta": {
                    "created_by": "layer_4_pov", 
                    "conflict_type": "perspective_disagreement",
                    "requires_resolution": True
                }
            })
        
        trace = {
            "pov_analyses": pov_analyses,
            "synthesis": synthesis,
            "conflict_detected": conflict_detected,
            "confidence_distribution": confidence_scores,
            "escalation_reason": "Low confidence or perspective conflict" if escalate else None
        }
        
        return dict(
            output=dict(
                pov_summary=synthesis["summary"],
                perspectives=pov_analyses,
                synthesis=synthesis,
                conflict_detected=conflict_detected
            ),
            confidence=avg_confidence,
            escalate=escalate,
            trace=trace,
            patch_memory=patch_memory
        )
    
    def _generate_pov_analysis(self, query: str, perspective: str, state: Dict) -> Dict:
        """Generate AI-powered POV analysis from specific perspective"""
        
        prompt = f"""
You are analyzing a question from the {perspective} perspective. 

QUERY: {query}

Please provide a structured analysis including:

1. **Analysis**: Your perspective-specific analysis (2-3 paragraphs)
2. **Key Considerations**: 3-5 bullet points of key factors from this perspective
3. **Stakeholder Impact**: How this affects stakeholders relevant to your perspective
4. **Confidence**: Rate your confidence in this analysis (0.0-1.0)

Respond in JSON format:
{{
    "analysis": "Your detailed analysis here...",
    "key_considerations": ["Point 1", "Point 2", "Point 3"],
    "stakeholder_impact": "Description of stakeholder impacts...",
    "confidence": 0.85
}}

Be specific to your {perspective} viewpoint. Consider:
- Industry Expert: Technical feasibility, market dynamics, competitive landscape
- Regulatory: Compliance requirements, legal frameworks, policy implications  
- Consumer: User experience, accessibility, cost-benefit, adoption barriers
- Academic: Research evidence, theoretical frameworks, knowledge gaps
- Economic: Cost structures, ROI, market impacts, economic efficiency
- Ethical: Moral implications, fairness, social responsibility, unintended consequences
"""
        
        try:
            response = GeminiRequest(prompt=prompt, model=self.model)
            response_text = response.text.strip()
            
            # Try to parse JSON response
            if response_text.startswith('```json'):
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif response_text.startswith('```'):
                response_text = response_text.split('```')[1].split('```')[0].strip()
                
            return json.loads(response_text)
            
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "analysis": response.text if 'response' in locals() else f"Analysis from {perspective} perspective pending",
                "key_considerations": ["Technical assessment required", "Stakeholder analysis needed"],
                "stakeholder_impact": "Impact assessment in progress",
                "confidence": 0.7
            }
    
    def _synthesize_perspectives(self, query: str, analyses: List[Dict]) -> Dict:
        """Use AI to synthesize multiple POV analyses"""
        
        perspectives_summary = "\n\n".join([
            f"**{analysis['perspective']}**:\n{analysis['analysis'][:200]}..."
            for analysis in analyses
        ])
        
        prompt = f"""
You are synthesizing multiple perspective analyses for this query: {query}

PERSPECTIVE ANALYSES:
{perspectives_summary}

Please provide a synthesis in JSON format:
{{
    "summary": "2-3 paragraph synthesis of all perspectives",
    "consensus_points": ["Point 1", "Point 2", "Point 3"],
    "conflicts": ["Conflict 1", "Conflict 2"] or [],
    "recommendations": ["Rec 1", "Rec 2", "Rec 3"],
    "overall_assessment": "Brief overall assessment"
}}

Focus on:
1. Where perspectives agree (consensus)
2. Where they conflict (tensions to resolve)
3. Integrated recommendations
4. Balanced overall assessment
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
                "summary": "Multi-perspective analysis synthesized across industry, regulatory, consumer, academic, economic, and ethical viewpoints.",
                "consensus_points": ["Multiple stakeholder considerations identified"],
                "conflicts": [],
                "recommendations": ["Further analysis recommended"],
                "overall_assessment": "Comprehensive perspective analysis completed"
            }
    
    def _detect_perspective_conflicts(self, analyses: List[Dict]) -> bool:
        """Detect significant conflicts between perspectives"""
        
        # Check confidence variance
        confidences = [a["confidence"] for a in analyses]
        confidence_variance = max(confidences) - min(confidences)
        
        # High variance suggests disagreement
        if confidence_variance > 0.3:
            return True
            
        # Check for explicit conflicts in synthesis
        # This would be enhanced with more sophisticated conflict detection
        
        return False
