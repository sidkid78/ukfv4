import asyncio
import os 
import logging 
from dataclasses import dataclass 
from google import genai 
from agents import set_default_openai_client, set_default_openai_api, set_tracing_disabled, set_tracing_export_api_key 

# Configure logging 
logger = logging.getLogger(__name__)

@dataclass 
class GeminiAgentConfig:
    """Configuration for Gemini deployments."""
    model: str = "gemini-2.5-pro-preview-03-25"

    def __post_init__(self):
        self.model = os.getenv("GEMINI_MODEL", self.model)

# Global configuration instance 
gemini_config = GeminiAgentConfig()

# Configure Gemini Client 
async def setup_gemini_client():
    """Set up Gemini client for the Agents SDK."""
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            client = genai.Client(api_key=api_key)

            set_default_openai_client(client)
            set_default_openai_api("generate_content")

            if not os.getenv("OPENAI_API_KEY"):
                set_tracing_disabled(True)
                logger.info("Tracing disabled - no OpenAI API key found")
            else:
                set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))
                logger.info("Tracing enabled with OpenAI API key")

            logger.info(f"Gemini client configured successfully with model: '{gemini_config.model}'")
            return True 
        
        except Exception as e:
            logger.error(f"Failed to configure Gemini client: {e}")
            return False 
        
    else:
        logger.warning("GEMINI_API_KEY not found in environment variables")
        return False 
    
if __name__ == "__main__":
    asyncio.run(setup_gemini_client())

