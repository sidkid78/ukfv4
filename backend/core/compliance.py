"""
Compliance Engine for UKG/USKD Simulation System
Enforces AGI safety, confidence thresholds, and containment protocols
"""

import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import logging

from core.audit import audit_logger, make_patch_certificate

logger = logging.getLogger(__name__)


class ComplianceViolation:
    """Represents a compliance violation"""
    
    def __init__(
        self, 
        violation_type: str, 
        severity: str, 
        description: str, 
        layer: int,
        details: Dict[str, Any] = None
    ):
        self.id = str(uuid.uuid4())
        self.violation_type = violation_type
        self.severity = severity
        self.description = description
        self.layer = layer
        self.details = details or {}
        self.timestamp = datetime.now()
        self.resolved = False
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "violation_type": self.violation_type,
            "severity": self.severity,
            "description": self.description,
            "layer": self.layer,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved
        }


class ComplianceRule:
    """Base class for compliance rules"""
    
    def __init__(self, rule_id: str, name: str, severity: str = "medium"):
        self.rule_id = rule_id
        self.name = name
        self.severity = severity
        self.enabled = True
        
    def check(
        self, 
        layer: int, 
        details: Dict[str, Any], 
        confidence: Optional[float] = None,
        persona: Optional[str] = None
    ) -> Optional[ComplianceViolation]:
        """Check if this rule is violated"""
        raise NotImplementedError
        
    def enable(self):
        self.enabled = True
        
    def disable(self):
        self.enabled = False


class ConfidenceThresholdRule(ComplianceRule):
    """Rule for minimum confidence thresholds"""
    
    def __init__(self, min_confidence: float = 0.995, layer_specific: Dict[int, float] = None):
        super().__init__("confidence_threshold", "Confidence Threshold Rule", "critical")
        self.min_confidence = min_confidence
        self.layer_specific = layer_specific or {}
        
    def check(
        self, 
        layer: int, 
        details: Dict[str, Any], 
        confidence: Optional[float] = None,
        persona: Optional[str] = None
    ) -> Optional[ComplianceViolation]:
        
        if confidence is None:
            return None
            
        # Get layer-specific threshold or default
        threshold = self.layer_specific.get(layer, self.min_confidence)
        
        # Apply stricter thresholds for safety-critical layers
        if layer >= 8:  # Layers 8-10 are safety critical
            threshold = max(threshold, 0.999)
        elif layer >= 5:  # Gatekeeper and above
            threshold = max(threshold, 0.998)
        
        if confidence < threshold:
            return ComplianceViolation(
                violation_type="confidence_below_threshold",
                severity=self.severity,
                description=f"Confidence {confidence:.4f} below required threshold {threshold:.4f}",
                layer=layer,
                details={
                    "confidence": confidence,
                    "threshold": threshold,
                    "shortfall": threshold - confidence
                }
            )
        
        return None


class AGISafetyRule(ComplianceRule):
    """Rule for AGI safety indicators"""
    
    def __init__(self):
        super().__init__("agi_safety", "AGI Safety Rule", "critical")
        self.safety_indicators = [
            "self_modification_detected",
            "recursive_improvement_detected", 
            "goal_divergence_detected",
            "emergence_indicators_present",
            "paradigm_shift_detected",
            "quantum_decoherence_detected"
        ]
        
    def check(
        self, 
        layer: int, 
        details: Dict[str, Any], 
        confidence: Optional[float] = None,
        persona: Optional[str] = None
    ) -> Optional[ComplianceViolation]:
        
        # Check for AGI safety indicators
        detected_indicators = []
        for indicator in self.safety_indicators:
            if details.get(indicator, False):
                detected_indicators.append(indicator)
        
        # Check for emergence detection
        if details.get("emergence_analysis", {}).get("emergence_detected", False):
            detected_indicators.append("emergence_detected")
        
        # Check for paradigm instability
        if details.get("meta_insights", {}).get("paradigm_instability_detected", False):
            detected_indicators.append("paradigm_instability")
        
        # Check for quantum decoherence
        if details.get("quantum_answer", {}).get("decoherence_detected", False):
            detected_indicators.append("quantum_decoherence")
        
        if detected_indicators:
            return ComplianceViolation(
                violation_type="agi_safety_violation",
                severity=self.severity,
                description=f"AGI safety indicators detected: {', '.join(detected_indicators)}",
                layer=layer,
                details={
                    "indicators": detected_indicators,
                    "indicator_count": len(detected_indicators),
                    "requires_containment": len(detected_indicators) > 1
                }
            )
        
        return None


class EthicalComplianceRule(ComplianceRule):
    """Rule for ethical compliance requirements"""
    
    def __init__(self):
        super().__init__("ethical_compliance", "Ethical Compliance Rule", "critical")
        
    def check(
        self, 
        layer: int, 
        details: Dict[str, Any], 
        confidence: Optional[float] = None,
        persona: Optional[str] = None
    ) -> Optional[ComplianceViolation]:
        
        # Check if ethical approval was denied
        if details.get("ethically_approved") is False:
            ethical_decision = details.get("ethical_decision", {})
            return ComplianceViolation(
                violation_type="ethical_approval_denied",
                severity=self.severity,
                description=f"Ethical approval denied: {ethical_decision.get('reason', 'Unknown reason')}",
                layer=layer,
                details={
                    "ethical_decision": ethical_decision,
                    "ethical_risks": details.get("ethical_risks", {}),
                    "requires_review": True
                }
            )
        
        # Check for high ethical risks
        ethical_risks = details.get("ethical_risks", {})
        if ethical_risks.get("risk_level") == "critical":
            return ComplianceViolation(
                violation_type="critical_ethical_risk",
                severity=self.severity,
                description="Critical ethical risks identified",
                layer=layer,
                details={
                    "risk_level": ethical_risks.get("risk_level"),
                    "critical_concerns": ethical_risks.get("critical_concerns", []),
                    "requires_mitigation": True
                }
            )
        
        return None


class MemoryIntegrityRule(ComplianceRule):
    """Rule for memory system integrity"""
    
    def __init__(self, max_patches_per_layer: int = 10, max_forks_per_layer: int = 5):
        super().__init__("memory_integrity", "Memory Integrity Rule", "high")
        self.max_patches_per_layer = max_patches_per_layer
        self.max_forks_per_layer = max_forks_per_layer
        
    def check(
        self, 
        layer: int, 
        details: Dict[str, Any], 
        confidence: Optional[float] = None,
        persona: Optional[str] = None
    ) -> Optional[ComplianceViolation]:
        
        violations = []
        
        # Check patch count
        patches = details.get("patches_applied", 0)
        if isinstance(patches, list):
            patches = len(patches)
        
        if patches > self.max_patches_per_layer:
            violations.append(f"Excessive patches: {patches} > {self.max_patches_per_layer}")
        
        # Check fork count
        forks = details.get("forks", [])
        if isinstance(forks, list) and len(forks) > self.max_forks_per_layer:
            violations.append(f"Excessive forks: {len(forks)} > {self.max_forks_per_layer}")
        
        # Check for memory corruption indicators
        if details.get("memory_corruption_detected", False):
            violations.append("Memory corruption detected")
        
        if violations:
            return ComplianceViolation(
                violation_type="memory_integrity_violation",
                severity=self.severity,
                description="; ".join(violations),
                layer=layer,
                details={
                    "patches": patches,
                    "forks": len(forks) if isinstance(forks, list) else 0,
                    "violations": violations
                }
            )
        
        return None


class SystemVerificationRule(ComplianceRule):
    """Rule for system verification requirements"""
    
    def __init__(self):
        super().__init__("system_verification", "System Verification Rule", "critical")
        
    def check(
        self, 
        layer: int, 
        details: Dict[str, Any], 
        confidence: Optional[float] = None,
        persona: Optional[str] = None
    ) -> Optional[ComplianceViolation]:
        
        # Only apply to Layer 9 (verification layer)
        if layer != 9:
            return None
            
        # Check if system verification failed
        if details.get("system_verified") is False:
            verification_decision = details.get("verification_decision", {})
            return ComplianceViolation(
                violation_type="system_verification_failed",
                severity=self.severity,
                description=f"System verification failed: {verification_decision.get('reason', 'Unknown reason')}",
                layer=layer,
                details={
                    "verification_decision": verification_decision,
                    "quality_assurance": details.get("quality_assurance", {}),
                    "requires_containment": True
                }
            )
        
        return None


class ComplianceEngine:
    """
    Main compliance engine that enforces all rules and triggers containment
    """
    
    def __init__(self):
        self.rules: List[ComplianceRule] = []
        self.violations: List[ComplianceViolation] = []
        self.containment_triggered = False
        self.containment_threshold = 2  # Number of critical violations to trigger containment
        
        # Initialize default rules
        self._initialize_default_rules()
        
    def _initialize_default_rules(self):
        """Initialize the default compliance rules"""
        
        # Confidence threshold rule
        confidence_rule = ConfidenceThresholdRule(
            min_confidence=0.995,
            layer_specific={
                5: 0.998,  # Gatekeeper layer
                8: 0.999,  # Ethics layer
                9: 0.9995, # Verification layer
                10: 1.0    # Containment layer
            }
        )
        self.rules.append(confidence_rule)
        
        # AGI safety rule
        agi_rule = AGISafetyRule()
        self.rules.append(agi_rule)
        
        # Ethical compliance rule
        ethical_rule = EthicalComplianceRule()
        self.rules.append(ethical_rule)
        
        # Memory integrity rule
        memory_rule = MemoryIntegrityRule()
        self.rules.append(memory_rule)
        
        # System verification rule
        verification_rule = SystemVerificationRule()
        self.rules.append(verification_rule)
        
        logger.info(f"Initialized {len(self.rules)} compliance rules")
    
    def add_rule(self, rule: ComplianceRule):
        """Add a custom compliance rule"""
        self.rules.append(rule)
        logger.info(f"Added compliance rule: {rule.name}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a compliance rule by ID"""
        for i, rule in enumerate(self.rules):
            if rule.rule_id == rule_id:
                removed_rule = self.rules.pop(i)
                logger.info(f"Removed compliance rule: {removed_rule.name}")
                return True
        return False
    
    def check_and_log(
        self, 
        layer: int, 
        details: Dict[str, Any], 
        confidence: Optional[float] = None,
        persona: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Check all compliance rules and log violations.
        Returns certificate if containment is triggered.
        """
        
        new_violations = []
        
        # Check all enabled rules
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            try:
                violation = rule.check(layer, details, confidence, persona)
                if violation:
                    new_violations.append(violation)
                    self.violations.append(violation)
                    
                    # Log the violation
                    logger.warning(f"Compliance violation: {violation.description}")
                    
                    # Create audit entry
                    audit_logger.log(
                        event_type="compliance_violation",
                        layer=layer,
                        details=violation.to_dict(),
                        confidence=confidence,
                        persona=persona
                    )
                    
            except Exception as e:
                logger.error(f"Error checking rule {rule.rule_id}: {e}")
        
        # Check if containment should be triggered
        critical_violations = [v for v in new_violations if v.severity == "critical"]
        
        if len(critical_violations) >= self.containment_threshold or self._should_trigger_containment(new_violations):
            return self._trigger_containment(layer, new_violations, details, persona)
        
        return None
    
    def _should_trigger_containment(self, violations: List[ComplianceViolation]) -> bool:
        """Determine if containment should be triggered"""
        
        # Immediate containment triggers
        immediate_triggers = [
            "agi_safety_violation",
            "ethical_approval_denied",
            "system_verification_failed"
        ]
        
        if any(v.violation_type in immediate_triggers for v in violations):
            return True
        
        # Accumulative triggers
        total_critical = sum(1 for v in self.violations[-10:] if v.severity == "critical")  # Last 10 violations
        if total_critical >= self.containment_threshold:
            return True
        
        return False
    
    def _trigger_containment(
        self, 
        layer: int, 
        violations: List[ComplianceViolation], 
        details: Dict[str, Any],
        persona: Optional[str] = None
    ) -> Dict[str, Any]:
        """Trigger containment protocol"""
        
        if self.containment_triggered:
            return None  # Already triggered
        
        self.containment_triggered = True
        
        containment_info = {
            "containment_id": str(uuid.uuid4()),
            "trigger_layer": layer,
            "trigger_violations": [v.to_dict() for v in violations],
            "total_violations": len(self.violations),
            "timestamp": datetime.now().isoformat(),
            "reason": "Compliance violations exceeded threshold"
        }
        
        # Create containment certificate
        cert = make_patch_certificate(
            event="containment",
            origin_layer=layer,
            data=containment_info,
            persona=persona
        )
        
        # Log containment trigger
        logger.critical(f"CONTAINMENT TRIGGERED at Layer {layer}")
        audit_logger.log(
            event_type="containment_trigger",
            layer=layer,
            details=containment_info,
            confidence=0.0,  # Zero confidence when containment triggered
            persona=persona,
            certificate=cert
        )
        
        return cert
    
    def get_violations(
        self, 
        severity: Optional[str] = None, 
        layer: Optional[int] = None,
        resolved: Optional[bool] = None
    ) -> List[ComplianceViolation]:
        """Get violations with optional filtering"""
        
        violations = self.violations
        
        if severity:
            violations = [v for v in violations if v.severity == severity]
        
        if layer is not None:
            violations = [v for v in violations if v.layer == layer]
        
        if resolved is not None:
            violations = [v for v in violations if v.resolved == resolved]
        
        return violations
    
    def resolve_violation(self, violation_id: str, resolution_note: str = "") -> bool:
        """Mark a violation as resolved"""
        
        for violation in self.violations:
            if violation.id == violation_id:
                violation.resolved = True
                violation.details["resolution_note"] = resolution_note
                violation.details["resolved_at"] = datetime.now().isoformat()
                
                logger.info(f"Resolved violation {violation_id}: {resolution_note}")
                return True
        
        return False
    
    def get_compliance_status(self) -> Dict[str, Any]:
        """Get overall compliance status"""
        
        total_violations = len(self.violations)
        unresolved_violations = len([v for v in self.violations if not v.resolved])
        critical_violations = len([v for v in self.violations if v.severity == "critical" and not v.resolved])
        
        # Determine status
        if self.containment_triggered:
            status = "contained"
        elif critical_violations > 0:
            status = "critical"
        elif unresolved_violations > 5:
            status = "warning"
        else:
            status = "compliant"
        
        return {
            "status": status,
            "containment_triggered": self.containment_triggered,
            "total_violations": total_violations,
            "unresolved_violations": unresolved_violations,
            "critical_violations": critical_violations,
            "active_rules": len([r for r in self.rules if r.enabled]),
            "last_check": datetime.now().isoformat()
        }
    
    def reset_containment(self, reason: str = "Manual reset"):
        """Reset containment status (use with extreme caution)"""
        
        if self.containment_triggered:
            logger.warning(f"Containment reset: {reason}")
            
            audit_logger.log(
                event_type="containment_reset",
                layer=0,
                details={
                    "reason": reason,
                    "previous_violations": len(self.violations),
                    "reset_by": "system"
                }
            )
            
            self.containment_triggered = False
    
    def clear_violations(self, older_than_hours: int = 24):
        """Clear old resolved violations"""
        
        cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
        
        before_count = len(self.violations)
        self.violations = [
            v for v in self.violations 
            if not v.resolved or v.timestamp.timestamp() > cutoff_time
        ]
        after_count = len(self.violations)
        
        if before_count > after_count:
            logger.info(f"Cleared {before_count - after_count} old violations")


# Global compliance engine instance
compliance_engine = ComplianceEngine()
