"""Layer-KA Mapping Configuration
Maps Knowledge Algorithms (KAs) to specific simulation layers"""

# Layer to KA mapping - determines which KAs are available to each layer
LAYER_KA_MAP = {
    1: [
        "sample_ka",           # Basic query processing
        "query_analyzer",      # Query analysis and parsing
        "intent_classifier"    # Intent classification
    ],
    
    2: [
        "sample_ka",           # Memory operations
        "memory_retriever",    # Advanced memory retrieval
        "knowledge_validator", # Knowledge validation
        "context_enricher"     # Context enrichment
    ],
    
    3: [
        "sample_ka",           # Research operations
        "research_coordinator", # Multi-agent research coordination
        "consensus_builder",   # Agent consensus building
        "hypothesis_generator" # Hypothesis generation
    ],
    
    4: [
        "perspective_analyzer", # POV analysis
        "stakeholder_mapper",  # Stakeholder identification
        "bias_detector",       # Bias detection and mitigation
        "triangulation_engine" # Perspective triangulation
    ],
    
    5: [
        "critical_evaluator",  # Critical analysis
        "assumption_validator", # Assumption validation
        "quality_assessor",    # Quality assessment
        "gatekeeper_filter"    # Gatekeeper filtering
    ],
    
    6: [
        "meta_reasoner",       # Meta-cognitive reasoning
        "synthesis_engine",    # Cross-domain synthesis
        "pattern_recognizer",  # Pattern recognition
        "insight_generator"    # Insight generation
    ],
    
    7: [
        "quantum_processor",   # Quantum reasoning
        "superposition_handler", # Hypothesis superposition
        "coherence_maintainer", # Quantum coherence
        "interference_analyzer" # Quantum interference
    ],
    
    8: [
        "ethics_evaluator",    # Ethical evaluation
        "impact_assessor",     # Societal impact assessment
        "harm_analyzer",       # Harm analysis
        "value_aligner"        # Value alignment
    ],
    
    9: [
        "system_verifier",     # System verification
        "integrity_checker",   # Integrity checking
        "coherence_validator", # Coherence validation
        "meta_analyzer"        # Meta-analysis
    ],
    
    10: [
        "emergence_detector",  # AGI emergence detection
        "containment_manager", # Containment management
        "safety_monitor",      # Safety monitoring
        "finalization_handler" # System finalization
    ]
}

# KA specialization mapping - maps KAs to their areas of expertise
KA_SPECIALIZATIONS = {
    # Layer 1 KAs
    "query_analyzer": {
        "type": "nlp",
        "capabilities": ["intent_detection", "complexity_analysis", "ambiguity_detection"],
        "confidence_boost": 0.05
    },
    
    "intent_classifier": {
        "type": "classification",
        "capabilities": ["query_classification", "domain_identification", "urgency_assessment"],
        "confidence_boost": 0.03
    },
    
    # Layer 2 KAs
    "memory_retriever": {
        "type": "memory",
        "capabilities": ["semantic_search", "relevance_ranking", "knowledge_synthesis"],
        "confidence_boost": 0.08
    },
    
    "knowledge_validator": {
        "type": "validation",
        "capabilities": ["fact_checking", "consistency_verification", "source_validation"],
        "confidence_boost": 0.10
    },
    
    "context_enricher": {
        "type": "enrichment",
        "capabilities": ["context_expansion", "background_integration", "detail_enhancement"],
        "confidence_boost": 0.06
    },
    
    # Layer 3 KAs
    "research_coordinator": {
        "type": "coordination",
        "capabilities": ["agent_orchestration", "task_distribution", "result_aggregation"],
        "confidence_boost": 0.12
    },
    
    "consensus_builder": {
        "type": "consensus",
        "capabilities": ["opinion_aggregation", "conflict_resolution", "agreement_finding"],
        "confidence_boost": 0.09
    },
    
    "hypothesis_generator": {
        "type": "generation",
        "capabilities": ["hypothesis_creation", "alternative_exploration", "scenario_building"],
        "confidence_boost": 0.07
    },
    
    # Layer 4 KAs
    "perspective_analyzer": {
        "type": "analysis",
        "capabilities": ["viewpoint_identification", "perspective_comparison", "bias_detection"],
        "confidence_boost": 0.11
    },
    
    "stakeholder_mapper": {
        "type": "mapping",
        "capabilities": ["stakeholder_identification", "influence_analysis", "interest_mapping"],
        "confidence_boost": 0.08
    },
    
    "bias_detector": {
        "type": "detection",
        "capabilities": ["cognitive_bias_detection", "systematic_bias_identification", "bias_mitigation"],
        "confidence_boost": 0.13
    },
    
    "triangulation_engine": {
        "type": "synthesis",
        "capabilities": ["perspective_synthesis", "convergence_analysis", "insight_triangulation"],
        "confidence_boost": 0.10
    },
    
    # Layer 5 KAs
    "critical_evaluator": {
        "type": "evaluation",
        "capabilities": ["critical_analysis", "weakness_identification", "strength_assessment"],
        "confidence_boost": 0.14
    },
    
    "assumption_validator": {
        "type": "validation",
        "capabilities": ["assumption_identification", "premise_checking", "logic_validation"],
        "confidence_boost": 0.12
    },
    
    "quality_assessor": {
        "type": "assessment",
        "capabilities": ["quality_measurement", "completeness_checking", "accuracy_assessment"],
        "confidence_boost": 0.11
    },
    
    "gatekeeper_filter": {
        "type": "filtering",
        "capabilities": ["safety_filtering", "appropriateness_checking", "risk_assessment"],
        "confidence_boost": 0.15
    },
    
    # Layer 6 KAs
    "meta_reasoner": {
        "type": "meta_cognitive",
        "capabilities": ["reasoning_about_reasoning", "cognitive_monitoring", "strategy_selection"],
        "confidence_boost": 0.16
    },
    
    "synthesis_engine": {
        "type": "synthesis",
        "capabilities": ["cross_domain_synthesis", "knowledge_integration", "pattern_synthesis"],
        "confidence_boost": 0.13
    },
    
    "pattern_recognizer": {
        "type": "recognition",
        "capabilities": ["pattern_detection", "similarity_analysis", "structure_identification"],
        "confidence_boost": 0.10
    },
    
    "insight_generator": {
        "type": "generation",
        "capabilities": ["insight_creation", "novel_connection_making", "breakthrough_identification"],
        "confidence_boost": 0.12
    },
    
    # Layer 7 KAs
    "quantum_processor": {
        "type": "quantum",
        "capabilities": ["superposition_processing", "quantum_reasoning", "probability_manipulation"],
        "confidence_boost": 0.18
    },
    
    "superposition_handler": {
        "type": "quantum",
        "capabilities": ["state_superposition", "hypothesis_superposition", "quantum_state_management"],
        "confidence_boost": 0.15
    },
    
    "coherence_maintainer": {
        "type": "quantum",
        "capabilities": ["quantum_coherence", "decoherence_prevention", "phase_management"],
        "confidence_boost": 0.17
    },
    
    "interference_analyzer": {
        "type": "quantum",
        "capabilities": ["interference_analysis", "constructive_interference", "destructive_interference"],
        "confidence_boost": 0.14
    },
    
    # Layer 8 KAs
    "ethics_evaluator": {
        "type": "ethics",
        "capabilities": ["ethical_analysis", "moral_reasoning", "value_assessment"],
        "confidence_boost": 0.20
    },
    "impact_assessor": {
        "type": "assessment",
        "capabilities": ["societal_impact", "consequence_analysis", "ripple_effect_assessment"],
        "confidence_boost": 0.16
    },
    
    "harm_analyzer": {
        "type": "safety",
        "capabilities": ["harm_identification", "risk_analysis", "safety_assessment"],
        "confidence_boost": 0.18
    },
    
    "value_aligner": {
        "type": "alignment",
        "capabilities": ["value_alignment", "goal_alignment", "preference_learning"],
        "confidence_boost": 0.19
    },
    
    # Layer 9 KAs
    "system_verifier": {
        "type": "verification",
        "capabilities": ["system_verification", "integrity_checking", "validation_processing"],
        "confidence_boost": 0.22
    },
    
    "integrity_checker": {
        "type": "checking",
        "capabilities": ["data_integrity", "logical_consistency", "structural_soundness"],
        "confidence_boost": 0.20
    },
    
    "coherence_validator": {
        "type": "validation",
        "capabilities": ["coherence_checking", "consistency_validation", "logical_flow_analysis"],
        "confidence_boost": 0.18
    },
    
    "meta_analyzer": {
        "type": "meta_analysis",
        "capabilities": ["meta_level_analysis", "higher_order_reasoning", "recursive_analysis"],
        "confidence_boost": 0.21
    },
    
    # Layer 10 KAs
    "emergence_detector": {
        "type": "detection",
        "capabilities": ["emergence_detection", "agi_indicators", "consciousness_detection"],
        "confidence_boost": 0.25
    },
    
    "containment_manager": {
        "type": "safety",
        "capabilities": ["containment_protocols", "safety_measures", "risk_mitigation"],
        "confidence_boost": 0.23
    },
    
    "safety_monitor": {
        "type": "monitoring",
        "capabilities": ["continuous_monitoring", "anomaly_detection", "safety_tracking"],
        "confidence_boost": 0.24
    },
    
    "finalization_handler": {
        "type": "finalization",
        "capabilities": ["system_finalization", "cleanup_procedures", "safe_shutdown"],
        "confidence_boost": 0.20
    }
}

# KA availability constraints
KA_CONSTRAINTS = {
    # Some KAs require certain conditions to be available
    "quantum_processor": {
        "requires": ["advanced_reasoning_conducted"],
        "minimum_layer": 7
    },
    
    "emergence_detector": {
        "requires": ["system_verification_attempted"],
        "minimum_layer": 10
    },
    
    "containment_manager": {
        "requires": ["safety_concerns_detected"],
        "minimum_layer": 10
    },
    
    "ethics_evaluator": {
        "requires": ["stakeholder_analysis_completed"],
        "minimum_layer": 8
    }
}

# Dynamic KA assignment based on context
DYNAMIC_KA_RULES = {
    # Rules for dynamically adding KAs based on simulation context
    "high_complexity_query": {
        "condition": lambda context: context.get("complexity", 0) > 0.7,
        "add_kas": ["meta_reasoner", "synthesis_engine"],
        "layers": [6, 7, 8, 9]
    },
    
    "safety_critical_domain": {
        "condition": lambda context: any(word in context.get("query", "").lower()
                                          for word in ["safety", "security", "risk", "harm"]),
        "add_kas": ["ethics_evaluator", "impact_assessor", "harm_analyzer"],
        "layers": [8, 9, 10]
    }
}
