#!/usr/bin/env python3
"""
Setup Script for UKG/USKD Simulation System with Gemini AI
Helps configure the environment and test the Gemini AI integration
"""

import os
import sys
import asyncio
from pathlib import Path

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    env_path = Path(".env")
    example_path = Path(".env.example")
    
    if env_path.exists():
        print("✅ .env file already exists")
        return True
    
    if not example_path.exists():
        print("❌ .env.example file not found")
        return False
    
    # Copy example to .env
    with open(example_path, 'r') as f:
        content = f.read()
    
    with open(env_path, 'w') as f:
        f.write(content)
    
    print("✅ Created .env file from template")
    print("⚠️  Please edit .env and add your GEMINI_API_KEY")
    return True

def check_gemini_api_key():
    """Check if Gemini API key is configured"""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("❌ GEMINI_API_KEY not configured")
        print("Please set your Gemini API key in the .env file")
        print("Get your API key from: https://makersuite.google.com/app/apikey")
        return False
    
    print("✅ Gemini API key configured")
    return True

async def test_gemini_connection():
    """Test connection to Gemini AI"""
    try:
        print("🔄 Testing Gemini AI connection...")
        
        # Import after environment is loaded
        from core.gemini_service import gemini_service, GeminiRequest, GeminiModel
        
        # Test with a simple request
        request = GeminiRequest(
            prompt="Hello! Please respond with 'AI connection successful' if you can read this.",
            model=GeminiModel.GEMINI_FLASH,
            temperature=0.1
        )
        
        response = await gemini_service.generate_async(request)
        
        if "successful" in response.content.lower():
            print("✅ Gemini AI connection successful!")
            print(f"   Response: {response.content}")
            print(f"   Model: {response.model}")
            print(f"   Confidence: {response.confidence}")
            return True
        else:
            print("⚠️  Gemini AI responded but with unexpected content:")
            print(f"   Response: {response.content}")
            return False
            
    except Exception as e:
        print(f"❌ Gemini AI connection failed: {str(e)}")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("🔄 Installing dependencies...")
    os.system("pip install -r requirements.txt")
    print("✅ Dependencies installed")

def main():
    """Main setup function"""
    print("🚀 UKG/USKD Simulation System Setup")
    print("=" * 50)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Install dependencies
    install_dependencies()
    
    # Create .env file
    if not create_env_file():
        sys.exit(1)
    
    # Check API key
    if not check_gemini_api_key():
        print("\n📝 Next steps:")
        print("1. Get a Gemini API key from: https://makersuite.google.com/app/apikey")
        print("2. Edit the .env file and replace 'your_gemini_api_key_here' with your actual API key")
        print("3. Run this setup script again to test the connection")
        sys.exit(1)
    
    # Test Gemini connection
    try:
        success = asyncio.run(test_gemini_connection())
        if not success:
            print("\n⚠️  Gemini AI test failed, but you can still proceed")
    except Exception as e:
        print(f"\n❌ Failed to test Gemini AI: {e}")
    
    print("\n🎉 Setup Complete!")
    print("\n📋 Next steps:")
    print("1. Start the backend server:")
    print("   cd backend && python -m uvicorn app.main:app --reload")
    print("2. Test the API:")
    print("   curl http://localhost:8000/health")
    print("3. Test Gemini AI:")
    print("   curl -X POST http://localhost:8000/api/ai/health")
    print("4. View API docs:")
    print("   http://localhost:8000/docs")

if __name__ == "__main__":
    main()
