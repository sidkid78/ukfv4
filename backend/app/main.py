"""
UKG/USKD Multi-Layered Simulation System - Backend Entry Point
FastAPI application with full API orchestration
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
import json

from api import simulation, agent, memory, plugin, audit, ui, axes, layer, trace
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
    
    yield
    
    logger.info("Shutting down UKG/USKD Simulation Engine...")

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="UKG/USKD Multi-Layered Simulation Engine",
        description="Advanced AGI-safe simulation system with layered reasoning",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # CORS middleware for frontend integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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
    app.include_router(axes.router, prefix="/api")
    app.include_router(layer.router, prefix="/api")
    app.include_router(trace.router, prefix="/api")  # Add trace router

    # WebSocket endpoint for real-time updates
    @app.websocket("/ws/{session_id}/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str, client_id: str):
        await websocket_manager.connect(websocket, client_id, session_id)
        try:
            while True:
                data = await websocket.receive_text()
                await websocket_manager.handle_client_message(client_id, json.loads(data))
        except WebSocketDisconnect:
            await websocket_manager.disconnect(client_id)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "UKG/USKD Simulation Engine",
            "plugins_loaded": len(ka_registry.get_ka_names())
        }
    
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
