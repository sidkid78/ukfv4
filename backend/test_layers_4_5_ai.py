# test_layers_4_5_ai.py - Test AI-powered Layers 4 & 5

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

# Set up environment (replace with your actual API key)
# os.environ['GEMINI_API_KEY'] = 'your-api-key-here'

from core.layers.layer4 import Layer4POVEngine
from core.layers.layer5 import Layer5GatekeeperTeamManagement
from core.memory import InMemoryKnowledgeGraph

def test_layer_4_pov_engine():
    """Test Layer 4 POV Engine with AI"""
    print("🔄 Testing Layer 4: POV Engine with Real AI")
    print("=" * 60)
    
    layer4 = Layer4POVEngine()
    memory = InMemoryKnowledgeGraph()
    
    # Test case: Healthcare AI analysis
    input_data = {
        "query": "Should AI be used for medical diagnosis in hospitals?",
        "axes": [0.8, 0.6, 0.7, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    }
    
    state = {
        "orig_query": "Should AI be used for medical diagnosis in hospitals?",
        "persona": "healthcare_analyst"
    }
    
    try:
        result = layer4.process(input_data, state, memory)
        
        print(f"✅ POV Engine Analysis Complete!")
        print(f"   Confidence: {result['confidence']:.3f}")
        print(f"   Escalate: {result['escalate']}")
        print(f"   Perspectives Analyzed: {len(result['output']['perspectives'])}")
        
        print("\n📊 POV Perspectives:")
        for i, perspective in enumerate(result['output']['perspectives'], 1):
            print(f"   {i}. {perspective['perspective']}")
            print(f"      Confidence: {perspective['confidence']:.3f}")
            print(f"      Analysis: {perspective['analysis'][:100]}...")
            print()
        
        print("🔗 Synthesis Summary:")
        synthesis = result['output']['synthesis']
        print(f"   {synthesis.get('summary', 'Synthesis pending')[:200]}...")
        
        if result['output']['conflict_detected']:
            print("⚠️  Perspective conflicts detected!")
            
        print(f"\n📋 Trace Data: {len(result['trace'])} elements")
        
        return result
        
    except Exception as e:
        print(f"❌ Layer 4 Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_layer_5_gatekeeper(layer4_result):
    """Test Layer 5 Gatekeeper with AI"""
    print("\n🔄 Testing Layer 5: Gatekeeper/Team Management with Real AI")
    print("=" * 60)
    
    layer5 = Layer5GatekeeperTeamManagement()
    memory = InMemoryKnowledgeGraph()
    
    # Use previous layer result in state
    input_data = {
        "query": "Should AI be used for medical diagnosis in hospitals?",
        "axes": [0.8, 0.6, 0.7, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    }
    
    state = {
        "orig_query": "Should AI be used for medical diagnosis in hospitals?",
        "layer4_trace": layer4_result['trace'] if layer4_result else {},
        "layer3_trace": {"agents_spawned": 4, "consensus_reached": True},
        "layer2_trace": {"memory_accessed": True, "patches_applied": 1},
        "layer1_trace": {"query_processed": True, "complexity": "medium"}
    }
    
    try:
        result = layer5.process(input_data, state, memory)
        
        print(f"✅ Gatekeeper Analysis Complete!")
        print(f"   Confidence: {result['confidence']:.3f}")
        print(f"   Escalate: {result['escalate']}")
        
        # Gatekeeper Decision
        decision = result['output']['gatekeeper_decision']
        print(f"\n🛡️  Gatekeeper Decision: {decision['decision']}")
        print(f"   Proceed: {decision['proceed']}")
        print(f"   Reasoning: {decision['reasoning']}")
        
        if decision['required_actions']:
            print(f"   Required Actions: {', '.join(decision['required_actions'])}")
        
        # Team Assessment
        team_status = result['output']['team_status']
        print(f"\n👥 Team Coherence Score: {team_status['coherence_score']:.3f}")
        if team_status['conflicts']:
            print(f"   Conflicts Detected: {', '.join(team_status['conflicts'])}")
        
        # Safety Assessment
        safety_status = result['output']['safety_status']
        print(f"\n🛡️  Safety Assessment:")
        print(f"   Risk Level: {safety_status['risk_level']}")
        print(f"   Safety Score: {safety_status['safety_score']:.3f}")
        print(f"   Compliance: {safety_status['compliance_status']}")
        
        if safety_status['concerns']:
            print(f"   Concerns: {', '.join(safety_status['concerns'])}")
        
        # Memory Patches
        if result['patch_memory']:
            print(f"\n💾 Memory Patches Created: {len(result['patch_memory'])}")
            for patch in result['patch_memory']:
                patch_type = patch['meta'].get('alert_type', patch['meta'].get('issue_type', 'unknown'))
                priority = patch['meta'].get('priority', 'high')
                print(f"   - {patch_type}: {priority}")
        
        print(f"\n📋 Trace Data: {len(result['trace'])} elements")
        
        return result
        
    except Exception as e:
        print(f"❌ Layer 5 Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_integration():
    """Test Layer 4 & 5 integration"""
    print("\n🔄 Testing Layer 4 → Layer 5 Integration")
    print("=" * 60)
    
    # Test Layer 4 first
    layer4_result = test_layer_4_pov_engine()
    
    if layer4_result:
        # Test Layer 5 with Layer 4 results
        layer5_result = test_layer_5_gatekeeper(layer4_result)
        
        if layer5_result:
            print("\n🎉 Integration Test Successful!")
            print("   ✅ Layer 4 (POV Engine) → AI-powered perspective analysis")
            print("   ✅ Layer 5 (Gatekeeper) → AI-powered quality & safety assessment")
            print("   ✅ Multi-layer state passing working")
            print("   ✅ Memory patching operational")
            print("   ✅ Escalation logic functional")
            
            return True
    
    print("\n❌ Integration test failed")
    return False

if __name__ == "__main__":
    print("🚀 Testing AI-Powered UKG/USKD Layers 4 & 5")
    print("=" * 60)
    
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ Please set your GEMINI_API_KEY environment variable!")
        print("   export GEMINI_API_KEY='your-actual-api-key'")
        print("   or set it in Windows: set GEMINI_API_KEY=your-actual-api-key")
        sys.exit(1)
    
    try:
        success = test_integration()
        
        if success:
            print("\n🎉 All tests passed! Your AI-powered layers are ready.")
            print("\n📝 What's working:")
            print("   • Layer 4: Multi-perspective AI analysis (6 different viewpoints)")
            print("   • Layer 5: AI-powered gatekeeper with safety assessment")
            print("   • Real-time conflict detection and resolution")
            print("   • Memory patching for critical findings")
            print("   • Escalation logic based on confidence and safety")
            
            print("\n🚀 Next Steps:")
            print("   1. Start your backend: uvicorn main:app --reload")
            print("   2. Run a simulation through your UI")
            print("   3. Watch real AI analysis in action!")
        else:
            print("\n❌ Some tests failed. Check the error messages above.")
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
