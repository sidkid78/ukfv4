"""
Layer 5: Gatekeeper Layer
Critical analysis, assumption validation, and quality assurance checkpoint
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import uuid

from .base import BaseLayer, LayerResult, register_layer
from core.memory import InMemoryKnowledgeGraph


@register_layer(5)
class Layer5Gatekeeper(BaseLayer):
    """
    Gatekeeper layer providing critical analysis, assumption validation,
    and quality assurance. Acts as a checkpoint before advanced reasoning layers.
    """
    
    def __init__(self):
        super().__init__()
        self.layer_number = 5
        self.layer_name = "Gatekeeper Layer"
        self.confidence_threshold = 0.995
        self.safety_critical = True
        self.requires_memory = True
        
    def process(
        self, 
        input_data: Dict[str, Any], 
        state: Dict[str, Any], 
        memory: InMemoryKnowledgeGraph,
        agents: Optional[List[Any]] = None
    ) -> LayerResult:
        """Perform critical gatekeeper analysis and validation"""
        
        query = input_data.get("normalized_query", input_data.get("query", ""))
        research_answer = input_data.get("research_answer")
        pov_synthesis = input_data.get("pov_synthesis", {})
        
        # Perform comprehensive validation
        validation_results = self._perform_comprehensive_validation(
            query, research_answer, pov_synthesis, input_data, memory
        )
        
        # Critical assumption analysis
        assumption_analysis = self._analyze_critical_assumptions(
            input_data, validation_results
        )
        
        # Quality assurance checks
        quality_assessment = self._assess_answer_quality(
            research_answer, pov_synthesis, validation_results
        )
        
        # Risk and safety evaluation
        risk_assessment = self._evaluate_risks_and_safety(
            query, input_data, validation_results
        )
        
        # Evidence sufficiency analysis
        evidence_analysis = self._analyze_evidence_sufficiency(
            input_data, validation_results
        )
        
        # Generate critical challenges and questions
        critical_challenges = self._generate_critical_challenges(
            validation_results, assumption_analysis, risk_assessment
        )
        
        # Determine if information passes gatekeeper criteria
        gatekeeper_decision = self._make_gatekeeper_decision(
            validation_results, quality_assessment, risk_assessment, evidence_analysis
        )
        
        # Calculate gatekeeper confidence
        confidence = self._calculate_gatekeeper_confidence(
            gatekeeper_decision, validation_results, quality_assessment
        )
        
        # Determine escalation need
        escalate = (
            not gatekeeper_decision["approved"] or
            self.should_escalate(confidence) or
            risk_assessment.get("high_risk", False) or
            len(critical_challenges) > 3
        )
        
        output = {
            **input_data,
            "gatekeeper_analysis_conducted": True,
            "validation_results": validation_results,
            "assumption_analysis": assumption_analysis,
            "quality_assessment": quality_assessment,
            "risk_assessment": risk_assessment,
            "evidence_analysis": evidence_analysis,
            "critical_challenges": critical_challenges,
            "gatekeeper_decision": gatekeeper_decision,
            "gatekeeper_approved": gatekeeper_decision["approved"],
            "gatekeeper_confidence": gatekeeper_decision.get("confidence"),
            "validated_answer": gatekeeper_decision.get("validated_answer")
        }
        
        trace = {
            "validation_checks": len(validation_results.get("checks_performed", [])),
            "assumptions_identified": len(assumption_analysis.get("assumptions", [])),
            "quality_score": quality_assessment.get("overall_score", 0),
            "risk_level": risk_assessment.get("risk_level", "unknown"),
            "evidence_sufficiency": evidence_analysis.get("sufficiency_level", "unknown"),
            "critical_issues": len(critical_challenges),
            "approved": gatekeeper_decision["approved"],
            "approval_conditions": gatekeeper_decision.get("conditions", [])
        }
        
        # Create forks for significant issues
        forks = []
        if not gatekeeper_decision["approved"] and gatekeeper_decision.get("fork_recommendation", False):
            forks = self._create_gatekeeper_forks(validation_results, critical_challenges)
        
        return LayerResult(
            output=output,
            confidence=confidence,
            escalate=escalate,
            trace=trace,
            forks=forks,
            metadata={"gatekeeper_layer": True, "safety_critical": True}
        )
    
    def _perform_comprehensive_validation(
        self, 
        query: str, 
        research_answer: str, 
        pov_synthesis: Dict[str, Any], 
        input_data: Dict[str, Any], 
        memory: InMemoryKnowledgeGraph
    ) -> Dict[str, Any]:
        """Perform comprehensive validation of all available information"""
        
        validation_checks = []
        
        # 1. Logical consistency check
        consistency_check = self._check_logical_consistency(research_answer, pov_synthesis)
        validation_checks.append(consistency_check)
        
        # 2. Internal coherence check
        coherence_check = self._check_internal_coherence(input_data)
        validation_checks.append(coherence_check)
        
        # 3. Evidence-reasoning alignment check
        alignment_check = self._check_evidence_reasoning_alignment(input_data)
        validation_checks.append(alignment_check)
        
        # 4. Completeness check
        completeness_check = self._check_answer_completeness(query, research_answer, pov_synthesis)
        validation_checks.append(completeness_check)
        
        # 5. Contradiction detection
        contradiction_check = self._detect_contradictions(input_data)
        validation_checks.append(contradiction_check)
        
        # 6. Source reliability assessment
        reliability_check = self._assess_source_reliability(input_data)
        validation_checks.append(reliability_check)
        
        # Calculate overall validation score
        passed_checks = sum(1 for check in validation_checks if check.get("passed", False))
        validation_score = passed_checks / len(validation_checks)
        
        # Identify critical failures
        critical_failures = [
            check for check in validation_checks 
            if not check.get("passed", False) and check.get("critical", False)
        ]
        
        return {
            "checks_performed": validation_checks,
            "validation_score": validation_score,
            "passed_checks": passed_checks,
            "total_checks": len(validation_checks),
            "critical_failures": critical_failures,
            "has_critical_failures": len(critical_failures) > 0,
            "validation_level": self._determine_validation_level(validation_score, critical_failures)
        }
    
    def _check_logical_consistency(self, research_answer: str, pov_synthesis: Dict[str, Any]) -> Dict[str, Any]:
        """Check for logical consistency between research and POV analysis"""
        
        if not research_answer or not pov_synthesis:
            return {
                "check_name": "logical_consistency",
                "passed": False,
                "critical": True,
                "reason": "Insufficient information for consistency check",
                "score": 0.0
            }
        
        # Simplified consistency check (would be more sophisticated in production)
        research_confidence = 0.8  # Would extract from research_answer metadata
        pov_confidence = pov_synthesis.get("confidence", 0.5)
        
        confidence_consistency = abs(research_confidence - pov_confidence) < 0.3
        
        return {
            "check_name": "logical_consistency",
            "passed": confidence_consistency,
            "critical": True,
            "reason": "Confidence levels between research and POV analysis are consistent" if confidence_consistency else "Significant confidence discrepancy detected",
            "score": 1.0 if confidence_consistency else 0.3,
            "details": {
                "research_confidence": research_confidence,
                "pov_confidence": pov_confidence,
                "difference": abs(research_confidence - pov_confidence)
            }
        }
    
    def _check_internal_coherence(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check internal coherence of the reasoning chain"""
        
        # Check if each layer builds logically on the previous
        layers_coherent = True
        coherence_issues = []
        
        # Check query -> research coherence
        if "research_answer" in input_data and "query" in input_data:
            if not input_data["research_answer"] or len(input_data["research_answer"]) < 10:
                layers_coherent = False
                coherence_issues.append("Research answer appears incomplete or missing")
        
        # Check research -> POV coherence
        if "pov_synthesis" in input_data and "research_answer" in input_data:
            pov_synthesis = input_data.get("pov_synthesis", {})
            if not pov_synthesis.get("answer") and input_data.get("research_answer"):
                layers_coherent = False
                coherence_issues.append("POV analysis missing despite research findings")
        
        return {
            "check_name": "internal_coherence",
            "passed": layers_coherent,
            "critical": True,
            "reason": "Reasoning chain is coherent" if layers_coherent else f"Coherence issues: {'; '.join(coherence_issues)}",
            "score": 1.0 if layers_coherent else 0.4,
            "issues": coherence_issues
        }
    
    def _check_evidence_reasoning_alignment(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if reasoning aligns with available evidence"""
        
        evidence_available = input_data.get("knowledge_available", False)
        research_conducted = input_data.get("research_conducted", False)
        pov_analysis = input_data.get("pov_analysis_conducted", False)
        
        # Evidence should support reasoning
        alignment_score = 0.0
        alignment_issues = []
        
        if evidence_available and research_conducted:
            alignment_score += 0.4
        elif not evidence_available and not research_conducted:
            alignment_issues.append("No evidence available and no research conducted")
        
        if pov_analysis and research_conducted:
            alignment_score += 0.3
        
        if input_data.get("research_answer") and input_data.get("pov_synthesis", {}).get("answer"):
            alignment_score += 0.3
        
        passed = alignment_score >= 0.6
        
        return {
            "check_name": "evidence_reasoning_alignment",
            "passed": passed,
            "critical": False,
            "reason": "Evidence aligns with reasoning" if passed else f"Alignment issues: {'; '.join(alignment_issues)}",
            "score": alignment_score,
            "issues": alignment_issues
        }
    
    def _check_answer_completeness(self, query: str, research_answer: str, pov_synthesis: Dict[str, Any]) -> Dict[str, Any]:
        """Check if the answer adequately addresses the query"""
        
        completeness_score = 0.0
        completeness_issues = []
        
        # Check if we have any answer at all
        has_research_answer = bool(research_answer and len(research_answer.strip()) > 10)
        has_pov_answer = bool(pov_synthesis.get("answer") and len(pov_synthesis["answer"].strip()) > 10)
        
        if has_research_answer:
            completeness_score += 0.5
        else:
            completeness_issues.append("Missing or insufficient research answer")
        
        if has_pov_answer:
            completeness_score += 0.3
        else:
            completeness_issues.append("Missing or insufficient POV analysis")
        
        # Check if answer addresses query complexity
        query_complexity = len(query.split()) / 10.0  # Simplified complexity metric
        if query_complexity > 0.5 and (not has_research_answer or not has_pov_answer):
            completeness_score *= 0.7
            completeness_issues.append("Complex query requires both research and POV analysis")
        
        # Bonus for having both types of analysis
        if has_research_answer and has_pov_answer:
            completeness_score += 0.2
        
        passed = completeness_score >= 0.7
        
        return {
            "check_name": "answer_completeness",
            "passed": passed,
            "critical": True,
            "reason": "Answer adequately addresses the query" if passed else f"Completeness issues: {'; '.join(completeness_issues)}",
            "score": min(1.0, completeness_score),
            "issues": completeness_issues
        }
    
    def _detect_contradictions(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect contradictions within the information"""
        
        contradictions = []
        
        # Check research vs POV contradictions
        research_answer = input_data.get("research_answer", "")
        pov_answer = input_data.get("pov_synthesis", {}).get("answer", "")
        
        if research_answer and pov_answer:
            # Simplified contradiction detection (would use NLP in production)
            research_positive = any(word in research_answer.lower() for word in ["yes", "positive", "beneficial", "good"])
            pov_positive = any(word in pov_answer.lower() for word in ["yes", "positive", "beneficial", "good"])
            
            research_negative = any(word in research_answer.lower() for word in ["no", "negative", "harmful", "bad"])
            pov_negative = any(word in pov_answer.lower() for word in ["no", "negative", "harmful", "bad"])
            
            if (research_positive and pov_negative) or (research_negative and pov_positive):
                contradictions.append("Research and POV analysis reach opposite conclusions")
        
        # Check confidence contradictions
        research_confidence = input_data.get("research_confidence", 0.5)
        pov_confidence = input_data.get("perspective_confidence", 0.5)
        
        if abs(research_confidence - pov_confidence) > 0.4:
            contradictions.append("Significant confidence discrepancy between analysis layers")
        
        passed = len(contradictions) == 0
        
        return {
            "check_name": "contradiction_detection",
            "passed": passed,
            "critical": True,
            "reason": "No contradictions detected" if passed else f"Contradictions found: {'; '.join(contradictions)}",
            "score": 1.0 if passed else max(0.2, 1.0 - len(contradictions) * 0.3),
            "contradictions": contradictions
        }
    
    def _assess_source_reliability(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the reliability of information sources"""
        
        reliability_score = 0.5  # Base score
        reliability_factors = []
        
        # Check if memory sources are available
        if input_data.get("knowledge_available", False):
            reliability_score += 0.2
            reliability_factors.append("Knowledge base available")
        
        # Check research quality
        if input_data.get("research_conducted", False):
            research_evidence = input_data.get("evidence_quality", "medium")
            if research_evidence == "high":
                reliability_score += 0.2
            elif research_evidence == "medium":
                reliability_score += 0.1
            reliability_factors.append(f"Research evidence quality: {research_evidence}")
        
        # Check POV analysis quality
        if input_data.get("pov_analysis_conducted", False):
            pov_quality = input_data.get("pov_synthesis", {}).get("synthesis_quality", "medium")
            if pov_quality == "high":
                reliability_score += 0.1
            reliability_factors.append(f"POV analysis quality: {pov_quality}")
        
        passed = reliability_score >= 0.7
        
        return {
            "check_name": "source_reliability",
            "passed": passed,
            "critical": False,
            "reason": "Sources demonstrate adequate reliability" if passed else "Source reliability concerns identified",
            "score": min(1.0, reliability_score),
            "factors": reliability_factors
        }
    
    def _determine_validation_level(self, validation_score: float, critical_failures: List[Dict]) -> str:
        """Determine overall validation level"""
        
        if len(critical_failures) > 0:
            return "failed"
        elif validation_score >= 0.9:
            return "excellent"
        elif validation_score >= 0.7:
            return "good"
        elif validation_score >= 0.5:
            return "acceptable"
        else:
            return "poor"
    
    def _analyze_critical_assumptions(
        self, 
        input_data: Dict[str, Any], 
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze critical assumptions underlying the reasoning"""
        
        assumptions = []
        
        # Query assumptions
        query = input_data.get("normalized_query", "")
        query_assumptions = self._extract_query_assumptions(query)
        assumptions.extend(query_assumptions)
        
        # Research assumptions
        if input_data.get("research_conducted", False):
            research_assumptions = self._extract_research_assumptions(input_data)
            assumptions.extend(research_assumptions)
        
        # POV assumptions
        if input_data.get("pov_analysis_conducted", False):
            pov_assumptions = self._extract_pov_assumptions(input_data)
            assumptions.extend(pov_assumptions)
        
        # Validate critical assumptions
        assumption_validation = []
        for assumption in assumptions:
            validation = self._validate_assumption(assumption, input_data)
            assumption_validation.append(validation)
        
        # Identify high-risk assumptions
        high_risk_assumptions = [
            val for val in assumption_validation 
            if val.get("risk_level") == "high"
        ]
        
        return {
            "assumptions": assumptions,
            "assumption_validation": assumption_validation,
            "high_risk_assumptions": high_risk_assumptions,
            "assumption_risk_level": "high" if len(high_risk_assumptions) > 2 else "medium" if len(high_risk_assumptions) > 0 else "low",
            "requires_assumption_validation": len(high_risk_assumptions) > 1
        }
    
    def _extract_query_assumptions(self, query: str) -> List[Dict[str, Any]]:
        """Extract assumptions embedded in the query"""
        
        assumptions = []
        query_lower = query.lower()
        
        # Detect assumption patterns
        if "should" in query_lower or "ought" in query_lower:
            assumptions.append({
                "type": "normative",
                "assumption": "There is a correct course of action",
                "text": query,
                "criticality": "medium"
            })
        
        if "will" in query_lower or "predict" in query_lower:
            assumptions.append({
                "type": "predictive",
                "assumption": "Future can be predicted from current information",
                "text": query,
                "criticality": "high"
            })
        
        if "best" in query_lower or "optimal" in query_lower:
            assumptions.append({
                "type": "optimization",
                "assumption": "Optimal solution exists and can be identified",
                "text": query,
                "criticality": "medium"
            })
        
        return assumptions
    
    def _extract_research_assumptions(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract assumptions from research analysis"""
        
        assumptions = []
        
        # Check research confidence assumptions
        research_confidence = input_data.get("research_confidence", 0.5)
        if research_confidence > 0.9:
            assumptions.append({
                "type": "confidence",
                "assumption": "Research evidence is highly reliable",
                "confidence": research_confidence,
                "criticality": "high"
            })
        
        # Check consensus assumptions
        consensus_analysis = input_data.get("consensus_analysis", {})
        if consensus_analysis.get("agreement_level") == "high":
            assumptions.append({
                "type": "consensus",
                "assumption": "Agent consensus indicates correctness",
                "evidence": consensus_analysis,
                "criticality": "medium"
            })
        
        return assumptions
    
    def _extract_pov_assumptions(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract assumptions from POV analysis"""
        
        assumptions = []
        
        pov_synthesis = input_data.get("pov_synthesis", {})
        
        # Check perspective completeness assumption
        if pov_synthesis.get("synthesis_quality") == "high":
            assumptions.append({
                "type": "completeness",
                "assumption": "All relevant perspectives have been considered",
                "evidence": pov_synthesis,
                "criticality": "high"
            })
        
        # Check bias mitigation assumption
        bias_analysis = input_data.get("bias_analysis", {})
        if bias_analysis.get("bias_risk_level") == "low":
            assumptions.append({
                "type": "bias_control",
                "assumption": "Biases have been adequately controlled",
                "evidence": bias_analysis,
                "criticality": "high"
            })
        
        return assumptions
    
    def _validate_assumption(self, assumption: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single assumption"""
        
        assumption_type = assumption.get("type", "unknown")
        criticality = assumption.get("criticality", "medium")
        
        # Assumption-specific validation logic
        if assumption_type == "predictive":
            # Predictive assumptions are inherently high-risk
            risk_level = "high"
            validation_status = "questionable"
            reasoning = "Predictive assumptions carry inherent uncertainty"
        
        elif assumption_type == "consensus":
            # Check if consensus is actually meaningful
            consensus_strength = input_data.get("consensus_analysis", {}).get("consensus_strength", 0.5)
            if consensus_strength > 0.8:
                risk_level = "low"
                validation_status = "supported"
            else:
                risk_level = "medium"
                validation_status = "weak_support"
            reasoning = f"Consensus strength: {consensus_strength:.2f}"
        
        elif assumption_type == "completeness":
            # Check for identified blind spots
            blind_spots = input_data.get("bias_analysis", {}).get("blind_spots", [])
            if len(blind_spots) > 2:
                risk_level = "high"
                validation_status = "challenged"
                reasoning = f"Multiple blind spots identified: {len(blind_spots)}"
            else:
                risk_level = "medium"
                validation_status = "acceptable"
                reasoning = "Limited blind spots identified"
        
        else:
            # Default validation
            risk_level = criticality
            validation_status = "unvalidated"
            reasoning = "Assumption requires domain-specific validation"
        
        return {
            "assumption": assumption,
            "validation_status": validation_status,
            "risk_level": risk_level,
            "reasoning": reasoning,
            "requires_attention": risk_level == "high" or validation_status in ["challenged", "questionable"]
        }
    
    def _assess_answer_quality(
        self, 
        research_answer: str, 
        pov_synthesis: Dict[str, Any], 
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess overall quality of the answer"""
        
        quality_factors = {}
        
        # Completeness factor
        completeness_check = next(
            (check for check in validation_results.get("checks_performed", []) 
             if check.get("check_name") == "answer_completeness"), 
            {}
        )
        quality_factors["completeness"] = completeness_check.get("score", 0.5)
        
        # Consistency factor
        consistency_check = next(
            (check for check in validation_results.get("checks_performed", []) 
             if check.get("check_name") == "logical_consistency"), 
            {}
        )
        quality_factors["consistency"] = consistency_check.get("score", 0.5)
        
        # Coherence factor
        coherence_check = next(
            (check for check in validation_results.get("checks_performed", []) 
             if check.get("check_name") == "internal_coherence"), 
            {}
        )
        quality_factors["coherence"] = coherence_check.get("score", 0.5)
        
        # Evidence alignment factor
        alignment_check = next(
            (check for check in validation_results.get("checks_performed", []) 
             if check.get("check_name") == "evidence_reasoning_alignment"), 
            {}
        )
        quality_factors["evidence_alignment"] = alignment_check.get("score", 0.5)
        
        # Calculate weighted overall score
        weights = {
            "completeness": 0.3,
            "consistency": 0.3,
            "coherence": 0.2,
            "evidence_alignment": 0.2
        }
        
        overall_score = sum(
            quality_factors[factor] * weights[factor] 
            for factor in weights
        )
        
        # Determine quality grade
        if overall_score >= 0.9:
            quality_grade = "excellent"
        elif overall_score >= 0.75:
            quality_grade = "good"
        elif overall_score >= 0.6:
            quality_grade = "acceptable"
        elif overall_score >= 0.4:
            quality_grade = "poor"
        else:
            quality_grade = "inadequate"
        
        return {
            "overall_score": overall_score,
            "quality_grade": quality_grade,
            "quality_factors": quality_factors,
            "meets_standards": overall_score >= 0.6,
            "improvement_areas": [
                factor for factor, score in quality_factors.items() 
                if score < 0.6
            ]
        }
    
    def _evaluate_risks_and_safety(
        self, 
        query: str, 
        input_data: Dict[str, Any], 
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate risks and safety concerns"""
        
        risks = []
        safety_concerns = []
        
        # Query-based risk assessment
        query_risks = self._assess_query_risks(query)
        risks.extend(query_risks)
        
        # Validation-based risks
        if validation_results.get("has_critical_failures", False):
            risks.append({
                "type": "validation_failure",
                "severity": "high",
                "description": "Critical validation failures detected",
                "impact": "unreliable_conclusions"
            })
        
        # Confidence-based risks
        research_confidence = input_data.get("research_confidence", 0.5)
        pov_confidence = input_data.get("perspective_confidence", 0.5)
        
        if research_confidence < 0.7 or pov_confidence < 0.7:
            risks.append({
                "type": "low_confidence",
                "severity": "medium",
                "description": "Low confidence in analysis results",
                "impact": "uncertain_reliability"
            })
        
        # Bias-based risks
        bias_analysis = input_data.get("bias_analysis", {})
        if bias_analysis.get("high_bias_risk", False):
            risks.append({
                "type": "bias_risk",
                "severity": "high",
                "description": "High risk of biased conclusions",
                "impact": "skewed_perspective"
            })
        
        # Safety-specific concerns
        if any(term in query.lower() for term in ["harm", "danger", "risk", "safety", "security"]):
            safety_concerns.append({
                "type": "safety_critical_domain",
                "severity": "high",
                "description": "Query involves safety-critical domain",
                "recommendation": "Enhanced validation required"
            })
        
        # Determine overall risk level
        high_severity_risks = [r for r in risks if r.get("severity") == "high"]
        
        if len(high_severity_risks) > 1:
            risk_level = "critical"
        elif len(high_severity_risks) == 1:
            risk_level = "high"
        elif len(risks) > 2:
            risk_level = "medium"
        elif len(risks) > 0:
            risk_level = "low"
        else:
            risk_level = "minimal"
        
        return {
            "risk_level": risk_level,
            "risks": risks,
            "safety_concerns": safety_concerns,
            "risk_summary": {
                "level": risk_level,
                "concerns": [r["description"] for r in risks],
                "recommendations": [r["recommendation"] for r in safety_concerns]
            }
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