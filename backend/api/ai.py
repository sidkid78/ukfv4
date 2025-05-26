"""
Gemini AI API Router
Handles Gemini AI configuration, health checks, and direct AI interactions
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from core.gemini_service import gemini_service, GeminiRequest, GeminiResponse, GeminiModel
from core.audit import audit_logger

router = APIRouter(prefix="/ai", tags=["gemini-ai"])

class DirectAIRequest(BaseModel):
    """Request for direct AI interaction"""
    prompt: str
    model: GeminiModel = GeminiModel.GEMINI_FLASH
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    persona: Optional[str] = None
    stream: bool = False

class AIHealthResponse(BaseModel):
    """AI service health response"""
    status: str
    models_available: List[str]
    response_time: Optional[float] = None
    last_check: str

@router.get("/health", response_model=AIHealthResponse)
async def get_ai_health():
    """Check Gemini AI service health"""
    try:
        health_check = await gemini_service.health_check()
        
        return AIHealthResponse(
            status=health_check["status"],
            models_available=[model.value for model in GeminiModel],
            response_time=health_check.get("response_time"),
            last_check=health_check["last_check"]
        )
    except Exception as e:
        return AIHealthResponse(
            status="unhealthy",
            models_available=[],
            last_check="error",
        )

@router.post("/generate", response_model=GeminiResponse)
async def generate_ai_response(
    request: DirectAIRequest,
    background_tasks: BackgroundTasks,
    session_id: Optional[str] = None
):
    """Generate AI response using Gemini"""
    try:
        # Convert to internal request format
        gemini_request = GeminiRequest(
            prompt=request.prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            system_prompt=request.system_prompt,
            persona=request.persona,
            stream=request.stream
        )
        
        # Generate response
        response = await gemini_service.generate_async(
            gemini_request,
            session_id=session_id
        )
        
        # Log interaction in background
        background_tasks.add_task(
            _log_direct_ai_interaction,
            request.dict(),
            response.dict(),
            session_id
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI generation failed: {str(e)}"
        )

@router.post("/analyze-query")
async def analyze_query_with_ai(
    query: str,
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None
):
    """Analyze a query using AI (similar to Layer 1 functionality)"""
    try:
        response = await gemini_service.analyze_query(
            query=query,
            context=context,
            session_id=session_id
        )
        
        return {
            "query": query,
            "analysis": response.content,
            "confidence": response.confidence,
            "processing_time": response.processing_time,
            "model_used": response.model
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query analysis failed: {str(e)}"
        )

@router.post("/research")
async def generate_research_with_ai(
    topic: str,
    persona: str = "domain_expert",
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None
):
    """Generate research content using AI (similar to Layer 3 functionality)"""
    try:
        response = await gemini_service.generate_research(
            topic=topic,
            persona=persona,
            context=context,
            session_id=session_id
        )
        
        return {
            "topic": topic,
            "persona": persona,
            "research": response.content,
            "confidence": response.confidence,
            "processing_time": response.processing_time,
            "model_used": response.model
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Research generation failed: {str(e)}"
        )

@router.post("/evaluate-confidence")
async def evaluate_content_confidence(
    content: str,
    criteria: List[str],
    session_id: Optional[str] = None
):
    """Evaluate confidence in content using AI"""
    try:
        response = await gemini_service.evaluate_confidence(
            content=content,
            criteria=criteria,
            session_id=session_id
        )
        
        return {
            "content_length": len(content),
            "criteria_count": len(criteria),
            "evaluation": response.content,
            "confidence": response.confidence,
            "processing_time": response.processing_time
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Confidence evaluation failed: {str(e)}"
        )

@router.get("/models")
async def list_available_models():
    """List available Gemini models"""
    return {
        "models": [
            {
                "name": model.value,
                "description": _get_model_description(model)
            }
            for model in GeminiModel
        ]
    }

@router.get("/usage-stats")
async def get_ai_usage_stats():
    """Get AI usage statistics (if implemented in service)"""
    try:
        # This would require implementing usage tracking in the service
        return {
            "message": "Usage statistics not yet implemented",
            "service_status": "active"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get usage stats: {str(e)}"
        )

@router.post("/safety-check")
async def check_content_safety(
    content: str,
    context: Optional[Dict[str, Any]] = None,
    layer: int = 0
):
    """Check content for safety using AI analysis"""
    try:
        # Use the existing safety analysis method from gemini_client
        from core.gemini_client import gemini_client
        
        safety_analysis = await gemini_client.safety_analysis(
            content=content,
            layer=layer,
            confidence=0.8,  # Default confidence
            context=context or {}
        )
        
        return {
            "content_length": len(content),
            "safety_analysis": safety_analysis,
            "safe": safety_analysis.get("safety_score", 0.5) > 0.7,
            "containment_needed": safety_analysis.get("containment_needed", False)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Safety check failed: {str(e)}"
        )

def _get_model_description(model: GeminiModel) -> str:
    """Get description for a Gemini model"""
    descriptions = {
        GeminiModel.GEMINI_PRO: "Most capable model for complex reasoning and analysis",
        GeminiModel.GEMINI_FLASH: "Fastest model for quick responses and simple tasks",
        GeminiModel.GEMINI_PRO_VISION: "Multimodal model capable of processing images and text"
    }
    return descriptions.get(model, "Gemini AI model")

async def _log_direct_ai_interaction(
    request_data: Dict[str, Any],
    response_data: Dict[str, Any],
    session_id: Optional[str]
):
    """Log direct AI interaction for audit purposes"""
    try:
        audit_logger.log(
            event_type="direct_ai_interaction",
            layer=0,  # Direct API call, not layer-specific
            details={
                "request": request_data,
                "response_summary": {
                    "model": response_data.get("model"),
                    "confidence": response_data.get("confidence"),
                    "processing_time": response_data.get("processing_time"),
                    "content_length": len(response_data.get("content", "")),
                },
                "session_id": session_id
            }
        )
    except Exception as e:
        # Don't fail the main request if logging fails
        print(f"Failed to log AI interaction: {e}")
