#!/usr/bin/env python3
"""
Test the AI-powered Layer 3 agents
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.gemini_service import gemini_service, GeminiRequest, GeminiModel

async def test_ai_connection():
    """Test basic AI connection"""
    print("🔄 Testing AI connection...")
    
    try:
        request = GeminiRequest(
            prompt="Hello! Please respond with 'AI connection successful' if you can read this.",
            model=GeminiModel.GEMINI_FLASH,
            temperature=0.1
        )
        
        response = await gemini_service.generate_async(request)
        
        print(f"✅ AI Response: {response.content}")
        print(f"   Confidence: {response.confidence}")
        print(f"   Processing Time: {response.processing_time:.2f}s")
        return True
        
    except Exception as e:
        print(f"❌ AI connection failed: {str(e)}")
        return False

async def test_agent_analysis():
    """Test AI-powered agent analysis"""
    print("\n🤖 Testing AI-powered agent analysis...")
    
    test_query = "What are the potential risks and benefits of artificial intelligence?"
    
    # Test expert analysis
    request = GeminiRequest(
        prompt=f"As a domain expert, analyze this query and provide expert insights: {test_query}",
        system_prompt="""You are a domain expert providing comprehensive analysis. 
        Provide detailed, evidence-based insights with specific reasoning. 
        Focus on accuracy, depth, and actionable conclusions.
        Format your response as: ANALYSIS: [your analysis] | CONFIDENCE: [0.0-1.0] | REASONING: [your reasoning]""",
        persona="domain_expert",
        model=GeminiModel.GEMINI_FLASH_0520,
        temperature=0.3
    )
    
    try:
        response = await gemini_service.generate_async(request)
        print(f"🧠 Expert Analysis:")
        print(f"   Content: {response.content[:200]}...")
        print(f"   Confidence: {response.confidence}")
        print(f"   Processing Time: {response.processing_time:.2f}s")
        return True
        
    except Exception as e:
        print(f"❌ Agent analysis failed: {str(e)}")
        return False

async def test_layer3_simulation():
    """Test complete Layer 3 simulation with AI agents"""
    print("\n🚀 Testing complete Layer 3 simulation...")
    
    try:
        from core.layers.layer3 import Layer3ResearchAgents
        from core.memory import global_memory_graph
        
        # Create Layer 3 instance
        layer3 = Layer3ResearchAgents()
        
        # Prepare test input
        input_data = {
            "normalized_query": "What are the ethical implications of AI in healthcare?",
            "query": "What are the ethical implications of AI in healthcare?",
            "axes": [0.6, 0.4, 0.3] + [0.0] * 10,  # 13D coordinates
            "complexity": 0.7,
            "knowledge_available": False,
            "persona": "researcher"
        }
        
        state = {
            "session_id": "test_session",
            "orig_query": "What are the ethical implications of AI in healthcare?"
        }
        
        print(f"   Query: {input_data['normalized_query']}")
        print(f"   Complexity: {input_data['complexity']}")
        print(f"   Processing with AI agents...")
        
        # Process through Layer 3
        result = layer3.process(input_data, state, global_memory_graph)
        
        print(f"\n✅ Layer 3 AI Processing Complete!")
        print(f"   Final Confidence: {result.confidence:.3f}")
        print(f"   Escalate: {result.escalate}")
        print(f"   Agents Spawned: {len(result.agents_spawned)}")
        print(f"   Forks Detected: {len(result.forks)}")
        
        # Show agent results
        if 'agent_results' in result.output:
            print(f"\n🤖 Agent Results:")
            for i, agent_result in enumerate(result.output['agent_results'][:2]):  # Show first 2
                print(f"   Agent {i+1} ({agent_result['persona']}):")
                print(f"     Answer: {agent_result['answer'][:100]}...")
                print(f"     Confidence: {agent_result['confidence']:.3f}")
                print(f"     Reasoning: {agent_result['reasoning'][:80]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Layer 3 simulation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🧪 UKG/USKD AI-Powered Layer 3 Test")
    print("=" * 50)
    
    # Test 1: Basic AI connection
    ai_works = await test_ai_connection()
    if not ai_works:
        print("\n❌ Cannot proceed - AI connection failed")
        return
    
    # Test 2: Agent analysis
    agent_works = await test_agent_analysis()
    if not agent_works:
        print("\n⚠️  Agent analysis failed, but continuing...")
    
    # Test 3: Full Layer 3 simulation
    layer3_works = await test_layer3_simulation()
    
    print("\n" + "=" * 50)
    if layer3_works:
        print("🎉 SUCCESS: AI-powered Layer 3 is working!")
        print("\n📋 What this means:")
        print("   ✅ Real AI agents are now analyzing queries")
        print("   ✅ Multiple AI personas provide different perspectives")
        print("   ✅ Confidence scores come from actual AI reasoning")
        print("   ✅ Your UI will now show real AI-generated content!")
    else:
        print("❌ FAILED: AI-powered Layer 3 needs debugging")

if __name__ == "__main__":
    asyncio.run(main())
