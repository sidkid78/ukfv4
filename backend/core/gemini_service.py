"""
Gemini AI Service for UKG/USKD Simulation System
Provides AI-powered reasoning, analysis, and knowledge processing capabilities
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, AsyncGenerator, Union, Callable
from datetime import datetime
from enum import Enum
import json
import os


from google import genai
from google.genai.types import HarmCategory, HarmBlockThreshold
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from google.genai import types

from core.audit import audit_logger, make_patch_certificate

logger = logging.getLogger(__name__)

class GeminiModel(str, Enum):
    """Available Gemini models"""
    GEMINI_FLASH_0520 = "gemini-2.5-flash-preview-05-20"
    GEMINI_FLASH = "gemini-2.0-flash"

class GeminiConfig(BaseSettings):
    """Gemini API configuration"""
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    gemini_default_model: GeminiModel = GeminiModel.GEMINI_FLASH
    gemini_max_retries: int = 3
    gemini_timeout: float = 400.0
    gemini_max_tokens: int = 8192
    gemini_temperature: float = 0.7
    
    top_p: float = 0.9
    top_k: int = 40
    
    # Add the extra fields
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8000
    fastapi_reload: bool = True
    allowed_origins: str = "*"
    log_level: str = "INFO"
    ws_max_connections: int = 100
    ws_heartbeat_interval: int = 30
    max_simulation_time: int = 300
    global_confidence_threshold: float = 0.995
    containment_threshold: float = 0.5
    max_layers: int = 10
    memory_max_cells: int = 10000
    memory_cleanup_interval: int = 3600
    audit_log_retention_days: int = 30
    audit_enable_certificates: bool = True
    plugin_auto_reload: bool = True
    plugin_safety_check: bool = True
    
    class Config:
        env_file = ".env"

class GeminiRequest(BaseModel):
    """Request model for Gemini API calls"""
    prompt: str
    model: GeminiModel = GeminiModel.GEMINI_FLASH
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    persona: Optional[str] = None
    stream: bool = False

class GeminiResponse(BaseModel):
    """Response model for Gemini API calls"""
    content: str
    model: str
    usage: Dict[str, Any] = {}
    confidence: float = 0.8
    reasoning_trace: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: str
    processing_time: float = 0.0
    
class GeminiService:
    def __init__(self, config: Optional[GeminiConfig] = None):
        self.config = config or GeminiConfig()
        os.environ["GEMINI_API_KEY"] = self.config.gemini_api_key
        self.client = genai.Client(api_key=self.config.gemini_api_key)
        self.safety_settings = [
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_MEDIUM_AND_ABOVE"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_MEDIUM_AND_ABOVE"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_MEDIUM_AND_ABOVE"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_MEDIUM_AND_ABOVE"
            ),
        ]
        self._last_request_time = 0
        self._min_request_interval = 0.1
        logger.info(f"Gemini service initialized with model: {self.config.gemini_default_model}")

    async def generate_async(self, request: GeminiRequest, session_id: Optional[str] = None, layer: Optional[int] = None) -> GeminiResponse:
        import uuid
        request_id = str(uuid.uuid4())
        start_time = time.time()
        try:
            await self._enforce_rate_limit()
            generation_config = types.GenerateContentConfig(
                temperature=request.temperature or self.config.gemini_temperature,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
                max_output_tokens=request.max_tokens or self.config.gemini_max_tokens,
                safety_settings=self.safety_settings,
            )
            full_prompt = self._build_prompt(request)
            response = self.client.models.generate_content(
                model=request.model.value,
                contents=full_prompt,
                config=generation_config,
            )
            content = getattr(response, 'text', '') or getattr(response.candidates[0], 'text', '')
            confidence = self._calculate_confidence(response, content)
            processing_time = time.time() - start_time
            return GeminiResponse(
                content=content,
                model=request.model.value,
                usage=self._extract_usage(response),
                confidence=confidence,
                reasoning_trace={
                    "prompt_length": len(full_prompt),
                    "response_length": len(content),
                    "model_used": request.model.value
                },
                request_id=request_id,
                processing_time=processing_time
            )
        except Exception as e:
            logger.error(f"Gemini request {request_id} failed: {str(e)}")
            return GeminiResponse(
                content=f"AI processing failed: {str(e)}",
                model=request.model.value,
                confidence=0.1,
                request_id=request_id,
                processing_time=time.time() - start_time,
                reasoning_trace={"error": str(e)}
            )

    async def generate_stream_async(
        self,
        request: GeminiRequest,
        session_id: Optional[str] = None,
        layer: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming AI response for real-time UI updates
        
        Args:
            request: The Gemini request parameters
            session_id: Optional simulation session ID
            layer: Optional layer number
            
        Yields:
            Streaming text chunks
        """
        import uuid
        request_id = str(uuid.uuid4())
        
        try:
            # Rate limiting
            await self._enforce_rate_limit()
            
            # Build generation config
            generation_config = types.GenerateContentConfig(
                temperature=request.temperature or self.config.gemini_temperature,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
                max_output_tokens=request.max_tokens or self.config.gemini_max_tokens,
                safety_settings=self.safety_settings,
            )
            
            # Build prompt
            full_prompt = self._build_prompt(request)
            
            # Generate streaming response
            response_stream = self.client.models.generate_content_stream(
                model=request.model.value,
                contents=full_prompt,
                config=generation_config,
            )
            
            full_content = ""
            for chunk in response_stream:
                if hasattr(chunk, 'text') and chunk.text:
                    full_content += chunk.text
                    yield chunk.text
            
            # Log completed stream
            audit_logger.log(
                event_type="ai_stream_complete",
                layer=layer or 0,
                details={
                    "request_id": request_id,
                    "model": request.model.value,
                    "session_id": session_id,
                    "total_length": len(full_content)
                }
            )
            
        except Exception as e:
            logger.error(f"Gemini streaming failed: {e}")
            yield f"[AI Streaming Error: {str(e)}]"
    
    def _build_prompt(self, request: GeminiRequest) -> str:
        parts = [
            f"SYSTEM: {request.system_prompt}" if request.system_prompt else
            "SYSTEM: You are an AI assistant in the UKG/USKD Simulation System. Provide helpful, safe responses."
        ]
        if request.persona:
            parts.append(f"PERSONA: {request.persona}")
        if request.context:
            parts.append(f"CONTEXT: {json.dumps(request.context, indent=2)}")
        parts.append(f"USER: {request.prompt}")
        return "\n\n".join(parts)

    async def _enforce_rate_limit(self):
        now = time.time()
        if now - self._last_request_time < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - (now - self._last_request_time))
        self._last_request_time = time.time()

    def _calculate_confidence(self, response: Any, content: str) -> float:
        score = 0.8
        if len(content) < 10:
            score -= 0.3
        elif len(content) > 500:
            score += 0.1
        return max(0.1, min(1.0, score))

    def _extract_usage(self, response: Any) -> Dict[str, Any]:
        usage = {}
        if hasattr(response, 'usage_metadata'):
            meta = response.usage_metadata
            usage = {
                "prompt_tokens": getattr(meta, 'prompt_token_count', 0),
                "completion_tokens": getattr(meta, 'candidates_token_count', 0),
                "total_tokens": getattr(meta, 'total_token_count', 0)
            }
        return usage

    
    async def _log_ai_interaction(self, request: GeminiRequest, response: GeminiResponse, session_id: Optional[str], layer: Optional[int]):
        audit_logger.log(
            event_type="ai_interaction",
            layer=layer or 0,
            details={
                "request_id": response.request_id,
                "model": request.model.value,
                "session_id": session_id,
                "prompt_length": len(request.prompt),
                "response_length": len(response.content),
                "confidence": response.confidence,
                "processing_time": response.processing_time,
                "usage": response.usage,
                "persona": request.persona
            },
            confidence=response.confidence,
            certificate=make_patch_certificate(
                event="ai_interaction",
                origin_layer=layer or 0,
                data={
                    "request_id": response.request_id,
                    "model": request.model.value,
                    "confidence": response.confidence
                }
            )
        )
    
    # Convenience methods for common AI tasks
    async def analyze_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> GeminiResponse:
        """Analyze a user query for intent and requirements"""
        request = GeminiRequest(
            prompt=f"Analyze this query for intent, requirements, and complexity: {query}",
            system_prompt="You are an expert query analyzer. Provide structured analysis.",
            context=context,
            model=GeminiModel.GEMINI_FLASH
        )
        return await self.generate_async(request, session_id, layer=1)
    
    async def generate_research(
        self,
        topic: str,
        persona: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> GeminiResponse:
        """Generate research content from a specific persona perspective"""
        request = GeminiRequest(
            prompt=f"Research and analyze: {topic}",
            system_prompt="Provide comprehensive research with sources and analysis.",
            persona=persona,
            context=context,
            model=GeminiModel.GEMINI_FLASH_0520
        )
        return await self.generate_async(request, session_id, layer=3)
    
    async def evaluate_confidence(
        self,
        content: str,
        criteria: List[str],
        session_id: Optional[str] = None
    ) -> GeminiResponse:
        """Evaluate confidence in content based on criteria"""
        criteria_str = "\n".join([f"- {c}" for c in criteria])
        request = GeminiRequest(
            prompt=f"Evaluate confidence in this content based on criteria:\n\nCONTENT: {content}\n\nCRITERIA:\n{criteria_str}",
            system_prompt="You are a confidence evaluation expert. Provide numerical confidence scores.",
            model=GeminiModel.GEMINI_FLASH
        )
        return await self.generate_async(request, session_id)

    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health status of the Gemini service
        
        Returns:
            Dict containing service health information
        """
        try:
            # Simple test request to verify service is working
            test_request = GeminiRequest(
                prompt="Test health check",
                model=GeminiModel.GEMINI_FLASH,
                max_tokens=10
            )
            
            response = await self.generate_async(test_request)
            
            return {
                "status": "healthy",
                "model": self.config.gemini_default_model.value,
                "api_available": True,
                "last_request_time": self._last_request_time,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "model": self.config.gemini_default_model.value,
                "api_available": False,
                "last_request_time": self._last_request_time,
                "error": str(e)
            }

# Global service instance
gemini_service = GeminiService()

# Export key classes and service
__all__ = [
    'GeminiService', 'GeminiRequest', 'GeminiResponse', 
    'GeminiModel', 'GeminiConfig', 'gemini_service'
]
