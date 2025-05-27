"""
Confidence and entropy calculation utilities for UKG/USKD simulation system
Provides realistic confidence scoring based on AI responses and simulation state
"""

import re
import math
from typing import Dict, Any, List, Optional
from datetime import datetime

class ConfidenceCalculator:
    """
    Calculates confidence scores for simulation layers based on various factors
    """
    
    def __init__(self):
        self.confidence_thresholds = {
            'excellent': 0.995,
            'good': 0.95,
            'moderate': 0.80,
            'low': 0.60,
            'critical': 0.40
        }
    
    def calculate_response_confidence(self, ai_response: str, prompt: str) -> float:
        """
        Calculate confidence based on AI response quality
        
        Args:
            ai_response: The AI-generated response text
            prompt: The original user prompt
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not ai_response or not ai_response.strip():
            return 0.1
        
        confidence_factors = []
        
        # Factor 1: Response length (longer responses generally more confident)
        length_score = min(len(ai_response) / 500, 1.0)  # Cap at 500 chars
        confidence_factors.append(length_score * 0.2)
        
        # Factor 2: Presence of specific indicators
        certainty_indicators = [
            r'\b(clearly|definitely|certainly|obviously|undoubtedly)\b',
            r'\b(therefore|thus|consequently|hence)\b',
            r'\b(evidence|research|studies|data)\b',
        ]
        
        uncertainty_indicators = [
            r'\b(might|maybe|perhaps|possibly|potentially)\b',
            r'\b(unclear|uncertain|ambiguous|confusing)\b',
            r'\b(I don\'t know|not sure|difficult to say)\b',
        ]
        
        certainty_count = sum(len(re.findall(pattern, ai_response, re.IGNORECASE)) 
                             for pattern in certainty_indicators)
        uncertainty_count = sum(len(re.findall(pattern, ai_response, re.IGNORECASE)) 
                               for pattern in uncertainty_indicators)
        
        certainty_score = min(certainty_count * 0.1, 0.3)
        uncertainty_penalty = min(uncertainty_count * 0.05, 0.2)
        
        confidence_factors.append(certainty_score - uncertainty_penalty)
        
        # Factor 3: Structure and coherence (simple heuristic)
        sentences = ai_response.split('.')
        avg_sentence_length = sum(len(s.strip().split()) for s in sentences) / max(len(sentences), 1)
        structure_score = min(avg_sentence_length / 20, 0.3)  # Optimal around 20 words per sentence
        confidence_factors.append(structure_score)
        
        # Factor 4: Relevance to prompt (keyword overlap)
        prompt_words = set(re.findall(r'\b\w+\b', prompt.lower()))
        response_words = set(re.findall(r'\b\w+\b', ai_response.lower()))
        
        if prompt_words:
            relevance_score = len(prompt_words.intersection(response_words)) / len(prompt_words)
            confidence_factors.append(relevance_score * 0.2)
        
        # Base confidence (never go below this)
        base_confidence = 0.6
        
        # Calculate final confidence
        calculated_confidence = base_confidence + sum(confidence_factors)
        
        # Clamp between 0.1 and 0.99 (never completely certain or uncertain)
        return max(0.1, min(0.99, calculated_confidence))
    
    def calculate_layer_confidence(
        self, 
        layer_number: int, 
        agents_active: int = 0,
        patches_applied: int = 0,
        forks_detected: int = 0,
        escalation_triggered: bool = False,
        ai_response: str = "",
        prompt: str = ""
    ) -> Dict[str, float]:
        """
        Calculate comprehensive confidence for a simulation layer
        
        Returns:
            Dict with score, entropy, and metadata
        """
        
        # Start with AI response confidence
        if ai_response and prompt:
            base_confidence = self.calculate_response_confidence(ai_response, prompt)
        else:
            base_confidence = 0.5 + (layer_number * 0.05)  # Slightly higher for later layers
        
        # Adjust based on simulation factors
        confidence_adjustments = []
        
        # More agents generally means higher confidence (consensus)
        if agents_active > 0:
            agent_boost = min(agents_active * 0.02, 0.1)  # Max 0.1 boost
            confidence_adjustments.append(agent_boost)
        
        # Patches indicate active learning/improvement
        if patches_applied > 0:
            patch_boost = min(patches_applied * 0.01, 0.05)
            confidence_adjustments.append(patch_boost)
        
        # Forks indicate uncertainty/conflict
        if forks_detected > 0:
            fork_penalty = min(forks_detected * 0.03, 0.15)
            confidence_adjustments.append(-fork_penalty)
        
        # Escalation indicates potential issues
        if escalation_triggered:
            confidence_adjustments.append(-0.1)
        
        # Layer-specific adjustments
        if layer_number <= 3:
            # Early layers are more uncertain
            confidence_adjustments.append(-0.05)
        elif layer_number >= 8:
            # Later layers should be more confident or trigger containment
            confidence_adjustments.append(0.05)
        
        final_confidence = base_confidence + sum(confidence_adjustments)
        
        # Calculate entropy (uncertainty measure)
        entropy = self.calculate_entropy(final_confidence, forks_detected, escalation_triggered)
        
        return {
            'score': max(0.05, min(0.999, final_confidence)),
            'entropy': entropy,
            'base_confidence': base_confidence,
            'adjustments': confidence_adjustments
        }
    
    def calculate_entropy(self, confidence: float, forks: int, escalation: bool) -> float:
        """
        Calculate entropy (uncertainty measure) for a layer
        
        Args:
            confidence: Current confidence score
            forks: Number of forks detected
            escalation: Whether escalation was triggered
            
        Returns:
            Entropy value between 0.0 and 1.0
        """
        # Base entropy is inverse of confidence
        base_entropy = 1.0 - confidence
        
        # Additional entropy from system instability
        fork_entropy = forks * 0.05
        escalation_entropy = 0.1 if escalation else 0.0
        
        total_entropy = base_entropy + fork_entropy + escalation_entropy
        
        # Clamp between 0.01 and 0.5 (some uncertainty always exists)
        return max(0.01, min(0.5, total_entropy))
    
    def calculate_confidence_delta(self, current_confidence: float, previous_confidence: float) -> float:
        """
        Calculate the change in confidence between layers
        
        Returns:
            Delta value (can be positive or negative)
        """
        if previous_confidence is None:
            return 0.0
        
        return current_confidence - previous_confidence
    
    def get_confidence_status(self, confidence: float) -> str:
        """
        Get human-readable confidence status
        """
        if confidence >= self.confidence_thresholds['excellent']:
            return 'EXCELLENT'
        elif confidence >= self.confidence_thresholds['good']:
            return 'GOOD'
        elif confidence >= self.confidence_thresholds['moderate']:
            return 'MODERATE'
        elif confidence >= self.confidence_thresholds['low']:
            return 'LOW'
        else:
            return 'CRITICAL'

# Global instance
confidence_calculator = ConfidenceCalculator()
