import asyncio
import os 
import logging 
from dataclasses import dataclass
from google import genai 
from agents import set_default_openai_client, set_default_openai_api, set_tracing_disabled, set_tracing_export_api_key 
from dotenv import load_dotenv

load_dotenv()
# Configure logging 
logger = logging.getLogger(__name__)

@dataclass 
class GeminiConfig:
    """Configuration for Gemini deployments."""
    programmable_deployment: str = "gemini-2.5-flash-preview-05-20"
    sub_agent_deployment: str = "gemini-2.0-flash"

    def __post_init__(self):
        self.programmable_deployment = os.getenv("GEMINI_PROGRAMMABLE_DEPLOYMENT", self.programmable_deployment)
        self.sub_agent_deployment = os.getenv("GEMINI_SUB_AGENT_DEPLOYMENT", self.sub_agent_deployment)

# Global configuration instance 
gemini_config = GeminiConfig()

# Configure Gemini Client once 
def setup_gemini_client():
    """Set up Gemini client for the OpenAI Agents SDK."""
    if os.getenv("GEMINI_API_KEY"):
        try:
            gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            set_default_openai_client(gemini_client)
            set_default_openai_api("generate_content")

            if not os.getenv("OPENAI_API_KEY"):
                set_tracing_disabled(True)
                logger.info("Tracing disabled - no OpenAI API key found")
            else:
                set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))
                logger.info("Tracing enabled with OpenAI API key")

            logger.info(f"Gemini client configured successfully with model: '{gemini_config.programmable_deployment}'")
            return True 
        
        except Exception as e:
            logger.error(f"Failed to configure Gemini client: {e}")
            return False 
        
    else:
        logger.warning("Gemini credentials not found in environment variables")
        return False 
            
setup_gemini_client()