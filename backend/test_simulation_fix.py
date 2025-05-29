#!/usr/bin/env python3
"""
Test script to demonstrate the simulation layer progression fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.simulation_engine import simulation_engine
from models.simulation import SimulationQuery

def test_simulation_progression():
    """Test that simulation now progresses through multiple layers"""
    print("Testing simulation layer progression...")
    
    # Create a test query
    query = SimulationQuery(
        user_query="What is artificial intelligence and how does it work?",
        axes=[0.0] * 13,
        context={}
    )
    
    print(f"Query: {query.user_query}")
    print(f"Global confidence threshold: {simulation_engine.global_confidence_threshold}")
    
    try:
        # Run simulation
        result = simulation_engine.run_simulation
        print(f"Simulation result: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
        
if __name__ == "__main__":
    test_simulation_progression()
    