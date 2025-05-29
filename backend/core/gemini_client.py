"""
Google Gemini AI Integration for UKG/USKD Simulation System
Provides advanced AI reasoning capabilities for layers, agents, and knowledge processing
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from google import genai
from google.genai.types import HarmCategory, HarmBlockThreshold
from google.genai import types
import json

logger = logging.getLogger(__name__)

class GeminiModel(str, Enum):
    """Available Gemini models"""
    GEMINI_FLASH_0520 = "gemini-2.5-flash-preview-05-20"
    GEMINI_FLASH = "gemini-2.0-flash"

class GeminiRole(str, Enum):
    """Roles for Gemini conversations"""
    USER = "user"
    MODEL = "model"
    SYSTEM = "system"

class GeminiRequest(BaseModel):
    """Request structure for Gemini API calls"""
    prompt: str
    model: GeminiModel = GeminiModel.GEMINI_FLASH_0520
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    safety_settings: Optional[Dict] = None

class GeminiResponse(BaseModel):
    """Response structure from Gemini API"""
    text: str
    model_used: GeminiModel
    usage: Dict[str, Any]
    confidence: float
    safety_ratings: List[Dict[str, Any]]
    generation_time: float
    metadata: Dict[str, Any]

class GeminiClient:
    """
    Advanced Gemini AI client for UKG/USKD simulation system
    Handles reasoning, analysis, and knowledge processing tasks
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini client with API key"""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable.")
        
        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)
        
        # Safety settings for AGI-safe operation
        self.default_safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        # Generation config
        self.default_generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        logger.info("Gemini client initialized successfully")
    
    async def generate_response(self, request: GeminiRequest) -> GeminiResponse:
        """
        Generate response using Gemini AI
        
        Args:
            request: GeminiRequest with prompt and configuration
            
        Returns:
            GeminiResponse with generated text and metadata
        """
        start_time = datetime.now()
        
        try:
            # Prepare generation config
            generation_config = types.GenerateContentConfig(
                temperature=request.temperature,
                top_p=self.default_generation_config["top_p"],
                top_k=self.default_generation_config["top_k"],
                max_output_tokens=request.max_tokens or self.default_generation_config["max_output_tokens"],
            )
            
            # Prepare safety settings
            safety_settings = request.safety_settings or self.default_safety_settings
            
            # Prepare prompt with system context if provided
            full_prompt = request.prompt
            if request.system_prompt:
                full_prompt = f"System: {request.system_prompt}\n\nUser: {request.prompt}"
            
            # Add context if provided
            if request.context:
                context_str = self._format_context(request.context)
                full_prompt = f"Context: {context_str}\n\n{full_prompt}"
            
            # Generate response using the latest SDK pattern
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=request.model.value,
                contents=full_prompt,
                config=generation_config,
                safety_settings=safety_settings
            )
            
            generation_time = (datetime.now() - start_time).total_seconds()
            
            # Extract response text
            response_text = response.text if response.text else ""
            
            # Calculate confidence (simplified heuristic)
            confidence = self._calculate_confidence(response)
            
            # Extract usage information
            usage = {
                "prompt_tokens": len(full_prompt.split()) * 1.3,  # Approximate
                "completion_tokens": len(response_text.split()) * 1.3,
                "total_tokens": (len(full_prompt) + len(response_text)) * 1.3
            }
            
            # Extract safety ratings
            safety_ratings = []
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                for rating in response.prompt_feedback.safety_ratings:
                    safety_ratings.append({
                        "category": rating.category.name,
                        "probability": rating.probability.name
                    })
            
            return GeminiResponse(
                text=response_text,
                model_used=request.model,
                usage=usage,
                confidence=confidence,
                safety_ratings=safety_ratings,
                generation_time=generation_time,
                metadata={
                    "prompt_length": len(full_prompt),
                    "response_length": len(response_text),
                    "temperature": request.temperature,
                    "timestamp": start_time.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {str(e)}")
            
            # Return error response
            return GeminiResponse(
                text=f"Error: {str(e)}",
                model_used=request.model,
                usage={"error": True},
                confidence=0.0,
                safety_ratings=[],
                generation_time=(datetime.now() - start_time).total_seconds(),
                metadata={"error": str(e), "timestamp": start_time.isoformat()}
            )
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary for prompt"""
        context_lines = []
        for key, value in context.items():
            if isinstance(value, (dict, list)):
                context_lines.append(f"{key}: {json.dumps(value, indent=2)}")
            else:
                context_lines.append(f"{key}: {value}")
        return "\n".join(context_lines)
    
    def _calculate_confidence(self, response) -> float:
        """Calculate confidence score based on response characteristics"""
        try:
            # Base confidence
            confidence = 0.8
            
            # Adjust based on response length (longer responses might be more confident)
            if response.text:
                text_length = len(response.text)
                if text_length > 100:
                    confidence += 0.1
                if text_length > 500:
                    confidence += 0.05
            
            # Adjust based on safety ratings (safer responses are more confident)
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                high_risk_count = 0
                for rating in response.prompt_feedback.safety_ratings:
                    if rating.probability.name in ['HIGH', 'MEDIUM']:
                        high_risk_count += 1
                
                if high_risk_count > 0:
                    confidence -= 0.2 * high_risk_count
            
            return max(0.1, min(0.99, confidence))
            
        except Exception:
            return 0.7  # Default confidence
    
    # Specialized methods for UKG/USKD simulation layers
    
    async def layer_reasoning(
        self, 
        layer_number: int,
        layer_name: str,
        input_data: Dict[str, Any],
        simulation_context: Dict[str, Any]
    ) -> GeminiResponse:
        """
        Perform layer-specific reasoning using Gemini
        """
        system_prompt = f"""
        You are an advanced AI reasoning system operating in Layer {layer_number} ({layer_name}) 
        of the UKG/USKD Multi-Layered Simulation System.
        
        Your role is to process the input data through this layer's specific reasoning patterns.
        Consider the simulation context and provide detailed analysis with confidence scoring.
        
        Layer {layer_number} specializes in: {self._get_layer_specialty(layer_number)}
        
        Provide your response in JSON format with:
        - analysis: detailed reasoning
        - confidence: numerical confidence score (0.0-1.0)
        - recommendations: next steps or escalation needs
        - metadata: additional context or flags
        """
        
        prompt = f"""
        Input Query: {input_data.get('user_query', 'No query provided')}
        
        Current Data: {json.dumps(input_data, indent=2)}
        
        Simulation Context: {json.dumps(simulation_context, indent=2)}
        
        Please analyze this information according to Layer {layer_number} requirements.
        """
        
        request = GeminiRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            model=GeminiModel.GEMINI_FLASH_0520,
            temperature=0.6,  # Lower temperature for more consistent reasoning
            context={"layer": layer_number, "simulation_context": simulation_context}
        )
        
        return await self.generate_response(request)
    
    async def agent_reasoning(
        self,
        agent_role: str,
        persona: str,
        task: str,
        context: Dict[str, Any]
    ) -> GeminiResponse:
        """
        Perform agent-specific reasoning and decision making
        """
        system_prompt = f"""
        You are an AI agent with the role of {agent_role} and persona {persona}.
        You are operating within the UKG/USKD simulation system.
        
        Your task is to analyze the given information from your specific perspective
        and provide reasoned conclusions, recommendations, or actions.
        
        Maintain your role and persona throughout the response.
        Consider potential conflicts, biases, or limitations in your perspective.
        """
        
        prompt = f"""
        Task: {task}
        
        Context: {json.dumps(context, indent=2)}
        
        As a {agent_role} with {persona} persona, please provide your analysis and recommendations.
        """
        
        request = GeminiRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            model=GeminiModel.GEMINI_FLASH_0520,  # Faster for agent responses
            temperature=0.8,  # Higher temperature for diverse agent perspectives
            context={"agent_role": agent_role, "persona": persona}
        )
        
        return await self.generate_response(request)
    
    async def safety_analysis(
        self,
        content: str,
        layer: int,
        confidence: float,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform safety analysis for AGI containment
        """
        system_prompt = """
        You are a safety analysis system for AGI containment in the UKG/USKD simulation.
        
        Analyze the provided content for potential safety risks, containment needs,
        or signs of dangerous AI behavior patterns.
        
        Focus on:
        - Confidence degradation patterns
        - Potential for recursive self-improvement
        - Evidence of goal misalignment
        - Signs of deceptive behavior
        - Containment trigger conditions
        
        Provide analysis in JSON format with safety_score (0.0-1.0) and recommendations.
        """
        
        prompt = f"""
        Content to analyze: {content}
        Layer: {layer}
        Confidence: {confidence}
        Context: {json.dumps(context, indent=2)}
        
        Perform comprehensive safety analysis.
        """
        
        request = GeminiRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            model=GeminiModel.GEMINI_FLASH_0520,
            temperature=0.3,  # Low temperature for consistent safety analysis
            context=context
        )
        
        response = await self.generate_response(request)
        
        try:
            # Try to parse JSON response
            safety_data = json.loads(response.text)
            return safety_data
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "safety_score": 0.5,
                "analysis": response.text,
                "recommendations": ["Manual review required"],
                "containment_needed": confidence < 0.5
            }
    
    def _get_layer_specialty(self, layer_number: int) -> str:
        """Get the specialty description for each layer"""
        specialties = {
            1: "Initial query parsing and axis anchoring",
            2: "Memory retrieval and knowledge graph operations",
            3: "Multi-agent research and collaborative reasoning",
            4: "Point-of-view analysis and perspective triangulation",
            5: "Advanced reasoning and pattern recognition",
            6: "Complex problem decomposition and solution synthesis",
            7: "Meta-cognitive analysis and recursive reasoning",
            8: "Safety monitoring and containment assessment",
            9: "Final integration and confidence validation",
            10: "Emergency containment and safety protocols"
        }
        return specialties.get(layer_number, "Advanced reasoning and analysis")
    
    # Utility methods
    
    def get_available_models(self) -> List[str]:
        """Get list of available Gemini models"""
        # The new SDK does not keep a models dict; return a static list or query the client if supported
        return [
            GeminiModel.GEMINI_FLASH_0520,
            GeminiModel.GEMINI_FLASH,
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if Gemini API is accessible and working"""
        try:
            test_request = GeminiRequest(
                prompt="Hello, this is a test. Please respond with 'OK' if you're working.",
                model=GeminiModel.GEMINI_FLASH_0520,
                temperature=0.1
            )
            
            response = await self.generate_response(test_request)
            
            return {
                "status": "healthy" if "ok" in response.text.lower() else "degraded",
                "response_time": response.generation_time,
                "models_available": len(self.get_available_models()),
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "models_available": 0,
                "last_check": datetime.now().isoformat()
            }

# Global Gemini client instance
gemini_client = GeminiClient()

# Export for use in other modules
__all__ = ['GeminiClient', 'GeminiRequest', 'GeminiResponse', 'GeminiModel', 'gemini_client']
