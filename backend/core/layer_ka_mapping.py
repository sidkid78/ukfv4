# File: C:\Users\sidki\source\repos\ukfv4\backend\core\layer_ka_mapping.py
# Layer to Knowledge Algorithm Mapping Configuration
# Defines which KAs (Knowledge Algorithms) are available for each simulation layer

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Static mapping: { layer_num: [ka_name1, ka_name2, ...] }
# This can be dynamically modified at runtime via API or configuration
LAYER_KA_MAP: Dict[int, List[str]] = {
    1: [
        'sample_ka',                    # Basic echo/entry processing
        'query_analyzer_ka',            # Input query analysis
    ],
    2: [
        'sample_ka',                    # Available in multiple layers
        'memory_retrieval_ka',          # Memory graph operations
        'context_builder_ka',           # Context assembly
    ],
    3: [
        'AdvancedReasoningKA',          # Advanced reasoning (from our sample plugin)
        'agent_coordinator_ka',         # Multi-agent coordination
        'research_ka',                  # Research and analysis
        'sample_ka',                    # Fallback option
    ],
    4: [
        'AdvancedReasoningKA',          # Multi-perspective analysis
        'pov_triangulation_ka',         # Point-of-view analysis
        'scenario_simulation_ka',       # Scenario modeling
        'stakeholder_analysis_ka',      # Stakeholder impact analysis
    ],
    5: [
        'gatekeeper_ka',                # Safety and validation
        'consensus_builder_ka',         # Team consensus mechanisms
        'conflict_resolution_ka',       # Handle disagreements
        'escalation_manager_ka',        # Escalation decision logic
    ],
    6: [
        'neural_simulation_ka',         # Neural network simulation
        'pattern_recognition_ka',       # Advanced pattern analysis
        'emergent_behavior_ka',         # Emergence detection
    ],
    7: [
        'recursive_reasoning_ka',       # Self-referential analysis
        'meta_cognitive_ka',            # Meta-level cognition
        'abstraction_engine_ka',        # Abstract concept handling
    ],
    8: [
        'quantum_superposition_ka',     # Quantum state analysis
        'parallel_universe_ka',         # Multi-reality modeling
        'temporal_analysis_ka',         # Time-based reasoning
        'dimensional_bridge_ka',        # Cross-dimensional analysis
    ],
    9: [
        'reality_synthesis_ka',         # Reality coherence management
        'consciousness_model_ka',       # Consciousness simulation
        'identity_fusion_ka',           # Identity integration
        'existential_validator_ka',     # Existential consistency checks
    ],
    10: [
        'containment_protocol_ka',      # AGI containment protocols
        'emergence_detector_ka',        # Emergence signal detection
        'safety_override_ka',           # Emergency safety systems
        'termination_sequence_ka',      # Controlled shutdown procedures
    ]
}

# Plugin priority within layers (higher number = higher priority)
KA_PRIORITY_MAP: Dict[str, int] = {
    # Layer 1 - Entry Processing
    'query_analyzer_ka': 10,
    'sample_ka': 1,
    
    # Layer 2 - Memory and Context
    'memory_retrieval_ka': 10,
    'context_builder_ka': 8,
    
    # Layer 3 - Research and Analysis
    'AdvancedReasoningKA': 15,
    'agent_coordinator_ka': 12,
    'research_ka': 10,
    
    # Layer 4 - Multi-perspective Analysis
    'pov_triangulation_ka': 12,
    'scenario_simulation_ka': 10,
    'stakeholder_analysis_ka': 8,
    
    # Layer 5 - Gatekeeper and Consensus
    'gatekeeper_ka': 20,           # High priority for safety
    'consensus_builder_ka': 15,
    'conflict_resolution_ka': 12,
    'escalation_manager_ka': 10,
    
    # Layer 6 - Neural Simulation
    'neural_simulation_ka': 15,
    'pattern_recognition_ka': 12,
    'emergent_behavior_ka': 10,
    
    # Layer 7 - Recursive Reasoning
    'recursive_reasoning_ka': 15,
    'meta_cognitive_ka': 12,
    'abstraction_engine_ka': 10,
    
    # Layer 8 - Quantum Analysis
    'quantum_superposition_ka': 15,
    'parallel_universe_ka': 12,
    'temporal_analysis_ka': 10,
    'dimensional_bridge_ka': 8,
    
    # Layer 9 - Reality Synthesis
    'reality_synthesis_ka': 20,
    'consciousness_model_ka': 15,
    'identity_fusion_ka': 12,
    'existential_validator_ka': 10,
    
    # Layer 10 - Containment and Safety
    'containment_protocol_ka': 25,     # Highest priority
    'emergence_detector_ka': 20,
    'safety_override_ka': 22,
    'termination_sequence_ka': 18,
}

# KA configuration parameters per algorithm
KA_CONFIG_MAP: Dict[str, Dict[str, any]] = {
    'sample_ka': {
        'timeout_seconds': 5,
        'max_retries': 3,
        'enable_caching': True,
    },
    'AdvancedReasoningKA': {
        'timeout_seconds': 30,
        'max_retries': 2,
        'confidence_threshold': 0.85,
        'max_reasoning_steps': 5,
        'enable_debugging': False,
        'parallel_processing': True,
    },
    'gatekeeper_ka': {
        'timeout_seconds': 15,
        'max_retries': 1,
        'safety_threshold': 0.95,
        'escalation_trigger': 0.7,
        'audit_mode': True,
    },
    'containment_protocol_ka': {
        'timeout_seconds': 10,
        'max_retries': 0,  # No retries for safety-critical operations
        'immediate_response': True,
        'bypass_cache': True,
        'audit_mode': True,
        'alert_threshold': 0.1,
    }
}

class LayerKAManager:
    """
    Manages the mapping between simulation layers and Knowledge Algorithms
    Provides dynamic configuration and runtime modification capabilities
    """
    
    def __init__(self):
        self.layer_map = LAYER_KA_MAP.copy()
        self.priority_map = KA_PRIORITY_MAP.copy()
        self.config_map = KA_CONFIG_MAP.copy()
        logger.info(f"Initialized LayerKAManager with {len(self.layer_map)} layer mappings")
    
    def get_kas_for_layer(self, layer: int) -> List[str]:
        """Get all KAs available for a specific layer"""
        return self.layer_map.get(layer, [])
    
    def get_priority_kas_for_layer(self, layer: int, limit: Optional[int] = None) -> List[str]:
        """Get KAs for a layer sorted by priority (highest first)"""
        kas = self.get_kas_for_layer(layer)
        sorted_kas = sorted(kas, key=lambda ka: self.priority_map.get(ka, 0), reverse=True)
        return sorted_kas[:limit] if limit else sorted_kas
    
    def add_ka_to_layer(self, layer: int, ka_name: str, priority: int = 5) -> bool:
        """Add a KA to a specific layer"""
        try:
            if layer not in self.layer_map:
                self.layer_map[layer] = []
            
            if ka_name not in self.layer_map[layer]:
                self.layer_map[layer].append(ka_name)
                self.priority_map[ka_name] = priority
                logger.info(f"Added KA '{ka_name}' to layer {layer} with priority {priority}")
                return True
            else:
                logger.warning(f"KA '{ka_name}' already exists in layer {layer}")
                return False
        except Exception as e:
            logger.error(f"Failed to add KA '{ka_name}' to layer {layer}: {e}")
            return False
    
    def remove_ka_from_layer(self, layer: int, ka_name: str) -> bool:
        """Remove a KA from a specific layer"""
        try:
            if layer in self.layer_map and ka_name in self.layer_map[layer]:
                self.layer_map[layer].remove(ka_name)
                logger.info(f"Removed KA '{ka_name}' from layer {layer}")
                return True
            else:
                logger.warning(f"KA '{ka_name}' not found in layer {layer}")
                return False
        except Exception as e:
            logger.error(f"Failed to remove KA '{ka_name}' from layer {layer}: {e}")
            return False
    
    def set_ka_priority(self, ka_name: str, priority: int) -> bool:
        """Set priority for a specific KA"""
        try:
            self.priority_map[ka_name] = priority
            logger.info(f"Set priority for KA '{ka_name}' to {priority}")
            return True
        except Exception as e:
            logger.error(f"Failed to set priority for KA '{ka_name}': {e}")
            return False
    
    def get_ka_config(self, ka_name: str) -> Dict[str, any]:
        """Get configuration for a specific KA"""
        return self.config_map.get(ka_name, {})
    
    def set_ka_config(self, ka_name: str, config: Dict[str, any]) -> bool:
        """Set configuration for a specific KA"""
        try:
            self.config_map[ka_name] = config
            logger.info(f"Updated configuration for KA '{ka_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to set config for KA '{ka_name}': {e}")
            return False
    
    def get_all_kas(self) -> List[str]:
        """Get list of all unique KAs across all layers"""
        all_kas = set()
        for kas in self.layer_map.values():
            all_kas.update(kas)
        return list(all_kas)
    
    def get_layers_for_ka(self, ka_name: str) -> List[int]:
        """Get all layers that use a specific KA"""
        layers = []
        for layer, kas in self.layer_map.items():
            if ka_name in kas:
                layers.append(layer)
        return sorted(layers)
    
    def validate_mapping(self) -> Dict[str, List[str]]:
        """Validate the current layer-KA mapping and return any issues"""
        issues = {
            'missing_kas': [],
            'empty_layers': [],
            'orphaned_priorities': [],
            'orphaned_configs': []
        }
        
        # Check for empty layers
        for layer, kas in self.layer_map.items():
            if not kas:
                issues['empty_layers'].append(f"Layer {layer}")
        
        # Check for orphaned priorities
        all_kas = self.get_all_kas()
        for ka_name in self.priority_map:
            if ka_name not in all_kas:
                issues['orphaned_priorities'].append(ka_name)
        
        # Check for orphaned configs
        for ka_name in self.config_map:
            if ka_name not in all_kas:
                issues['orphaned_configs'].append(ka_name)
        
        return issues
    
    def export_mapping(self) -> Dict[str, any]:
        """Export current mapping configuration"""
        return {
            'layer_map': self.layer_map,
            'priority_map': self.priority_map,
            'config_map': self.config_map,
            'metadata': {
                'total_layers': len(self.layer_map),
                'total_kas': len(self.get_all_kas()),
                'exported_at': None  # Would be timestamp in real implementation
            }
        }
    
    def import_mapping(self, mapping_data: Dict[str, any]) -> bool:
        """Import mapping configuration"""
        try:
            if 'layer_map' in mapping_data:
                self.layer_map = mapping_data['layer_map']
            if 'priority_map' in mapping_data:
                self.priority_map = mapping_data['priority_map']
            if 'config_map' in mapping_data:
                self.config_map = mapping_data['config_map']
            
            logger.info("Successfully imported layer-KA mapping configuration")
            return True
        except Exception as e:
            logger.error(f"Failed to import mapping configuration: {e}")
            return False

# Global instance for use throughout the application
layer_ka_manager = LayerKAManager()

# Convenience functions for direct access
def get_kas_for_layer(layer: int) -> List[str]:
    """Get KAs for a specific layer"""
    return layer_ka_manager.get_kas_for_layer(layer)

def get_priority_kas_for_layer(layer: int, limit: Optional[int] = None) -> List[str]:
    """Get priority-sorted KAs for a layer"""
    return layer_ka_manager.get_priority_kas_for_layer(layer, limit)

def get_ka_config(ka_name: str) -> Dict[str, any]:
    """Get configuration for a KA"""
    return layer_ka_manager.get_ka_config(ka_name)

# Example usage and testing
if __name__ == "__main__":
    print("Layer-KA Mapping Configuration")
    print("=" * 40)
    
    # Display mapping
    for layer in sorted(LAYER_KA_MAP.keys()):
        kas = get_priority_kas_for_layer(layer)
        print(f"Layer {layer}: {kas}")
    
    print("\nValidation Results:")
    issues = layer_ka_manager.validate_mapping()
    for issue_type, items in issues.items():
        if items:
            print(f"  {issue_type}: {items}")
    
    print(f"\nTotal KAs: {len(layer_ka_manager.get_all_kas())}")
    print(f"Layers configured: {len(LAYER_KA_MAP)}")