def advanced_reasoning_meta():
    """Plugin metadata - describes the plugin's capabilities and configuration"""
    return {
        "name": "AdvancedReasoningKA",
        "description": "Advanced multi-step reasoning algorithm with confidence scoring",
        "version": "1.2.0",
        "author": "UKG Simulation Team",
        "type": "KA",
        "layers": [2, 3, 4], 
        "active": True,
        "params": {
            "confidence_threshold": 0.85,
            "max_reasoning_steps": 5,
            "enable_debugging": False
        }
    }

def advanced_reasoning_runner(slice_input: dict, context: dict) -> dict:
    """
    Main plugin execution function
    
    Args:
        slice_input: Input data from the simulation layer
        context: Additional context from the simulation state
        
    Returns:
        dict: Plugin output with required fields
    """
    
  