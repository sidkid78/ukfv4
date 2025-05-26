# backend/main.py
"""
UKG/USKD Multi-Layered Simulation System - Backend Entry Point
FastAPI application with full API orchestration including Gemini AI integration
"""

import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
import json
import uuid

from dotenv import load_dotenv

load_dotenv()

from api import simulation, agent, memory, plugin, audit, ui, ai
from core.plugin_loader import ka_registry
from core.websocket_manager import websocket_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting UKG/USKD Simulation Engine...")
    
    # Initialize plugin registry
    ka_registry.load_plugins()
    logger.info(f"Loaded {len(ka_registry.get_ka_names())} knowledge algorithms")
    
    # Test Gemini AI connection
    try:
        from core.gemini_service import gemini_service
        health = await gemini_service.health_check()
        logger.info(f"Gemini AI service status: {health.get('status', 'unknown')}")
    except Exception as e:
        logger.warning(f"Gemini AI service initialization warning: {e}")
    
    yield
    
    logger.info("Shutting down UKG/USKD Simulation Engine...")

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="UKG/USKD Multi-Layered Simulation Engine",
        description="Advanced AGI-safe simulation system with layered reasoning and Gemini AI integration",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # CORS middleware for frontend integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("ALLOWED_ORIGINS"),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(simulation.router, prefix="/api")
    app.include_router(agent.router, prefix="/api")
    app.include_router(memory.router, prefix="/api")
    app.include_router(plugin.router, prefix="/api")
    app.include_router(audit.router, prefix="/api")
    app.include_router(ui.router, prefix="/api")
    app.include_router(ai.router, prefix="/api")  # Add Gemini AI router
    
    # WebSocket endpoint for real-time simulation updates
    @app.websocket("/ws/{session_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str):
        """WebSocket endpoint for real-time simulation updates"""
        client_id = str(uuid.uuid4())
        
        # Connect client to session
        connected = await websocket_manager.connect(websocket, client_id, session_id)
        if not connected:
            logger.error(f"Failed to connect client {client_id} to session {session_id}")
            return
        
        try:
            # Listen for client messages
            while True:
                data = await websocket.receive_text()
                try:
                    message_data = json.loads(data)
                    await websocket_manager.handle_client_message(client_id, message_data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from client {client_id}: {data}")
                except Exception as e:
                    logger.error(f"Error processing message from client {client_id}: {e}")
                    
        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected from session {session_id}")
        except Exception as e:
            logger.error(f"WebSocket error for client {client_id}: {e}")
        finally:
            # Clean up connection
            await websocket_manager.disconnect(client_id)
    
    # WebSocket stats endpoint for monitoring
    @app.get("/api/websocket/stats")
    async def websocket_stats():
        """Get WebSocket connection statistics"""
        return websocket_manager.get_session_stats()
    
    # Enhanced health check endpoint with AI status
    @app.get("/health")
    async def health_check():
        """Comprehensive health check including AI services"""
        health_data = {
            "status": "healthy",
            "service": "UKG/USKD Simulation Engine",
            "plugins_loaded": len(ka_registry.get_ka_names()),
            "websocket_connections": len(websocket_manager.connections),
            "ai_service": "unknown"
        }
        
        # Check AI service health
        try:
            from core.gemini_service import gemini_service
            ai_health = await gemini_service.health_check()
            health_data["ai_service"] = ai_health.get("status", "unknown")
            health_data["ai_models"] = len([model for model in ["gemini-pro", "gemini-flash"]])
        except Exception as e:
            health_data["ai_service"] = "unavailable"
            health_data["ai_error"] = str(e)
        
        return health_data
    
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
