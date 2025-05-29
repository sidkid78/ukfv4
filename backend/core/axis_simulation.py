# core/axis_simulation.py - Axis-driven persona simulation

from typing import Dict, Any, List
import logging

def simulate_axis_driven_persona(input_axis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Multidimensional simulation: expands personas, returns mapping, activation, and traversal log.
    
    This function takes axis coordinates and simulates how different personas would
    interact with the knowledge space defined by those coordinates.
    """
    
    try:
        # Extract axis information
        pillar = input_axis.get('pillar', 'PL01')
        sector = input_axis.get('sector', '0000')
        location = input_axis.get('location', 'US')
        role_knowledge = input_axis.get('role_knowledge', 'General Analyst')
        role_sector = input_axis.get('role_sector', 'Domain Expert')
        
        # Simulate persona expansion based on axis coordinates
        expanded_personas = _generate_persona_expansions(input_axis)
        
        # Generate axis mapping
        axis_mapping = _generate_axis_mapping(input_axis)
        
        # Simulate activation patterns
        activation_patterns = _simulate_activation_patterns(input_axis, expanded_personas)
        
        # Create traversal log
        traversal_log = _generate_traversal_log(input_axis, expanded_personas, activation_patterns)
        
        return {
            "status": "success",
            "input_axis": input_axis,
            "expanded_personas": expanded_personas,
            "axis_mapping": axis_mapping,
            "activation_patterns": activation_patterns,
            "traversal_log": traversal_log,
            "simulation_metadata": {
                "total_personas": len(expanded_personas),
                "active_dimensions": len([v for v in input_axis.values() if v]),
                "complexity_score": _calculate_complexity_score(input_axis)
            }
        }
        
    except Exception as e:
        logging.error(f"Axis simulation error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "input_axis": input_axis
        }

def _generate_persona_expansions(input_axis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate expanded personas based on axis coordinates"""
    
    base_personas = [
        "Domain Expert", "Regulatory Specialist", "Compliance Officer", 
        "Research Analyst", "Industry Consultant", "Policy Advisor"
    ]
    
    expanded_personas = []
    
    for persona in base_personas:
        expanded_persona = {
            "name": persona,
            "axis_alignment": _calculate_persona_axis_alignment(persona, input_axis),
            "knowledge_domains": _get_persona_knowledge_domains(persona, input_axis),
            "activation_strength": _calculate_activation_strength(persona, input_axis),
            "specializations": _get_persona_specializations(persona, input_axis)
        }
        expanded_personas.append(expanded_persona)
    
    return expanded_personas

def _generate_axis_mapping(input_axis: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive axis mapping"""
    
    return {
        "primary_dimensions": {
            "pillar": input_axis.get('pillar', 'PL01'),
            "sector": input_axis.get('sector', '0000'),
            "location": input_axis.get('location', 'US')
        },
        "role_dimensions": {
            "knowledge_role": input_axis.get('role_knowledge'),
            "sector_role": input_axis.get('role_sector'),
            "regulatory_role": input_axis.get('role_regulatory'),
            "compliance_role": input_axis.get('role_compliance')
        },
        "contextual_dimensions": {
            "regulatory": input_axis.get('regulatory'),
            "compliance": input_axis.get('compliance'),
            "temporal": input_axis.get('temporal')
        },
        "derived_dimensions": {
            "honeycomb": input_axis.get('honeycomb', []),
            "branch": input_axis.get('branch'),
            "node": input_axis.get('node')
        }
    }

def _simulate_activation_patterns(input_axis: Dict[str, Any], personas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Simulate how different personas activate in the axis space"""
    
    patterns = {}
    
    for persona in personas:
        persona_name = persona["name"]
        activation_strength = persona["activation_strength"]
        
        patterns[persona_name] = {
            "activation_level": activation_strength,
            "primary_focus": _determine_primary_focus(persona, input_axis),
            "secondary_interests": _determine_secondary_interests(persona, input_axis),
            "interaction_style": _determine_interaction_style(persona, input_axis)
        }
    
    return patterns

def _generate_traversal_log(input_axis: Dict[str, Any], personas: List[Dict[str, Any]], 
                          activation_patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate a log of how personas traverse the axis space"""
    
    log_entries = []
    
    # Initial axis entry
    log_entries.append({
        "step": 1,
        "action": "axis_entry",
        "description": f"Entered axis space at {input_axis.get('pillar', 'PL01')}",
        "active_personas": [p["name"] for p in personas if p["activation_strength"] > 0.5]
    })
    
    # Persona activation
    for i, persona in enumerate(personas, 2):
        if persona["activation_strength"] > 0.3:
            log_entries.append({
                "step": i,
                "action": "persona_activation",
                "persona": persona["name"],
                "description": f"{persona['name']} activated with strength {persona['activation_strength']:.2f}",
                "focus_areas": persona.get("knowledge_domains", [])
            })
    
    # Cross-dimensional traversal
    if input_axis.get('honeycomb'):
        log_entries.append({
            "step": len(log_entries) + 1,
            "action": "cross_dimensional_traversal",
            "description": "Traversing honeycomb connections",
            "connections": input_axis.get('honeycomb')
        })
    
    return log_entries

def _calculate_persona_axis_alignment(persona: str, input_axis: Dict[str, Any]) -> float:
    """Calculate how well a persona aligns with the given axis coordinates"""
    
    alignment_scores = {
        "Domain Expert": 0.9 if input_axis.get('role_sector') else 0.6,
        "Regulatory Specialist": 0.9 if input_axis.get('regulatory') else 0.4,
        "Compliance Officer": 0.9 if input_axis.get('compliance') else 0.4,
        "Research Analyst": 0.8,  # Always relatively high
        "Industry Consultant": 0.7 if input_axis.get('sector') else 0.5,
        "Policy Advisor": 0.8 if input_axis.get('location') else 0.6
    }
    
    return alignment_scores.get(persona, 0.5)

def _get_persona_knowledge_domains(persona: str, input_axis: Dict[str, Any]) -> List[str]:
    """Get knowledge domains for a persona based on axis coordinates"""
    
    base_domains = {
        "Domain Expert": ["Industry Analysis", "Technical Expertise"],
        "Regulatory Specialist": ["Legal Frameworks", "Policy Analysis"],
        "Compliance Officer": ["Standards", "Audit Procedures"],
        "Research Analyst": ["Data Analysis", "Research Methods"],
        "Industry Consultant": ["Business Strategy", "Market Analysis"],
        "Policy Advisor": ["Public Policy", "Stakeholder Management"]
    }
    
    domains = base_domains.get(persona, ["General Knowledge"])
    
    # Add axis-specific domains
    if input_axis.get('pillar'):
        domains.append(f"Pillar {input_axis['pillar']} Expertise")
    if input_axis.get('sector'):
        domains.append(f"Sector {input_axis['sector']} Knowledge")
    
    return domains

def _calculate_activation_strength(persona: str, input_axis: Dict[str, Any]) -> float:
    """Calculate activation strength for a persona in the given axis space"""
    
    base_strength = _calculate_persona_axis_alignment(persona, input_axis)
    
    # Boost strength based on role matches
    if persona == "Domain Expert" and input_axis.get('role_sector'):
        base_strength += 0.2
    elif persona == "Regulatory Specialist" and input_axis.get('role_regulatory'):
        base_strength += 0.2
    elif persona == "Compliance Officer" and input_axis.get('role_compliance'):
        base_strength += 0.2
    
    return min(1.0, base_strength)

def _get_persona_specializations(persona: str, input_axis: Dict[str, Any]) -> List[str]:
    """Get specializations for a persona based on axis coordinates"""
    
    specializations = []
    
    if input_axis.get('pillar'):
        specializations.append(f"{input_axis['pillar']} Systems")
    if input_axis.get('sector'):
        specializations.append(f"Sector {input_axis['sector']} Applications")
    if input_axis.get('location'):
        specializations.append(f"{input_axis['location']} Regional Expertise")
    
    return specializations

def _determine_primary_focus(persona: Dict[str, Any], input_axis: Dict[str, Any]) -> str:
    """Determine primary focus for a persona in the axis space"""
    
    persona_name = persona["name"]
    
    focus_map = {
        "Domain Expert": f"Technical analysis of {input_axis.get('pillar', 'system')}",
        "Regulatory Specialist": f"Regulatory compliance for {input_axis.get('regulatory', 'framework')}",
        "Compliance Officer": f"Standards adherence for {input_axis.get('compliance', 'requirements')}",
        "Research Analyst": f"Data-driven analysis of {input_axis.get('sector', 'domain')}",
        "Industry Consultant": f"Strategic guidance for {input_axis.get('sector', 'industry')}",
        "Policy Advisor": f"Policy implications in {input_axis.get('location', 'jurisdiction')}"
    }
    
    return focus_map.get(persona_name, "General analysis")

def _determine_secondary_interests(persona: Dict[str, Any], input_axis: Dict[str, Any]) -> List[str]:
    """Determine secondary interests for a persona"""
    
    interests = []
    
    # Add cross-dimensional interests
    if input_axis.get('honeycomb'):
        interests.append("Cross-dimensional relationships")
    if input_axis.get('temporal'):
        interests.append("Temporal analysis")
    if input_axis.get('branch'):
        interests.append("Hierarchical structures")
    
    return interests

def _determine_interaction_style(persona: Dict[str, Any], input_axis: Dict[str, Any]) -> str:
    """Determine how a persona interacts in the axis space"""
    
    persona_name = persona["name"]
    
    styles = {
        "Domain Expert": "Deep technical analysis",
        "Regulatory Specialist": "Compliance-focused review",
        "Compliance Officer": "Standards-based assessment",
        "Research Analyst": "Data-driven investigation",
        "Industry Consultant": "Strategic consultation",
        "Policy Advisor": "Policy-oriented guidance"
    }
    
    return styles.get(persona_name, "General analysis")

def _calculate_complexity_score(input_axis: Dict[str, Any]) -> float:
    """Calculate complexity score based on axis dimensions"""
    
    complexity = 0.0
    
    # Base complexity for filled dimensions
    filled_dimensions = len([v for v in input_axis.values() if v])
    complexity += filled_dimensions * 0.1
    
    # Additional complexity for specific patterns
    if input_axis.get('honeycomb') and len(input_axis['honeycomb']) > 1:
        complexity += 0.2
    if input_axis.get('temporal'):
        complexity += 0.15
    if input_axis.get('regulatory') and input_axis.get('compliance'):
        complexity += 0.25
    
    return min(1.0, complexity)
