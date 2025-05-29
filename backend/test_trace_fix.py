#!/usr/bin/env python3
"""
Quick test to verify trace logging is working properly
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_simulation_and_traces():
    print("🧪 Testing UKG/USKD simulation and trace logging...")
    
    # Step 1: Start a simulation
    print("\n1️⃣ Starting simulation...")
    start_payload = {
        "prompt": "What is the future of AI safety?",
        "context": {"test": True}
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/simulation/start", json=start_payload)
        if response.status_code == 200:
            data = response.json()
            session_id = data["session"]["id"]
            print(f"✅ Simulation started successfully!")
            print(f"   Session ID: {session_id}")
            print(f"   AI Response: {data['content'][:100]}...")
        else:
            print(f"❌ Failed to start simulation: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error starting simulation: {e}")
        return
    
    # Step 2: Check if traces were created
    print(f"\n2️⃣ Checking traces for session {session_id}...")
    try:
        response = requests.get(f"{API_BASE}/api/trace/get/{session_id}")
        if response.status_code == 200:
            traces = response.json()
            print(f"✅ Found {len(traces)} trace entries!")
            
            for i, trace in enumerate(traces):
                print(f"   [{i+1}] {trace.get('timestamp', 'No time')} - Layer {trace.get('layer', '?')}: {trace.get('message', 'No message')[:80]}...")
        else:
            print(f"❌ Failed to get traces: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error getting traces: {e}")
        return
    
    # Step 3: Try stepping the simulation
    print(f"\n3️⃣ Stepping simulation to next layer...")
    try:
        response = requests.post(f"{API_BASE}/api/simulation/step/{session_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Simulation stepped successfully!")
            print(f"   New layer: {data.get('layer', 'Unknown')}")
        else:
            print(f"⚠️ Step failed (expected for demo): {response.status_code}")
    except Exception as e:
        print(f"⚠️ Step error (expected for demo): {e}")
    
    # Step 4: Check traces again
    print(f"\n4️⃣ Checking traces again after step...")
    try:
        response = requests.get(f"{API_BASE}/api/trace/get/{session_id}")
        if response.status_code == 200:
            traces = response.json()
            print(f"✅ Now found {len(traces)} trace entries!")
            
            # Show the latest traces
            for i, trace in enumerate(traces[-3:]):  # Show last 3
                print(f"   [{len(traces)-2+i}] {trace.get('timestamp', 'No time')} - Layer {trace.get('layer', '?')}: {trace.get('message', 'No message')[:80]}...")
        else:
            print(f"❌ Failed to get traces: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting traces: {e}")
    
    print(f"\n✨ Test complete! Session ID: {session_id}")
    print(f"   You can now visit: http://localhost:3000/simulation/{session_id}")

if __name__ == "__main__":
    test_simulation_and_traces()
