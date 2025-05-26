"""
WebSocket Manager for UKG/USKD Simulation System
Handles real-time communication for simulation updates, layer progression,
agent actions, trace logs, fork events, and audit notifications.
"""

import json
import logging
from typing import Dict, List, Set, Any, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
from enum import Enum
from pydantic import BaseModel
import uuid

logger = logging.getLogger(__name__)

class MessageType(str, Enum):
    """WebSocket message types for the simulation system"""
    # Simulation Events
    SIMULATION_STARTED = "simulation_started"
    SIMULATION_COMPLETED = "simulation_completed"
    SIMULATION_ERROR = "simulation_error"
    
    # Layer Events
    LAYER_STARTED = "layer_started"
    LAYER_COMPLETED = "layer_completed"
    LAYER_ESCALATED = "layer_escalated"
    LAYER_CONTAINED = "layer_contained"
    
    # Agent Events
    AGENT_SPAWNED = "agent_spawned"
    AGENT_ACTION = "agent_action"
    AGENT_KILLED = "agent_killed"
    AGENT_VOTE = "agent_vote"
    
    # Memory/Patch Events
    MEMORY_PATCHED = "memory_patched"
    MEMORY_FORKED = "memory_forked"
    
    # Trace Events
    TRACE_LOG = "trace_log"
    AUDIT_EVENT = "audit_event"
    
    # Compliance/Safety Events
    CONFIDENCE_THRESHOLD = "confidence_threshold"
    CONTAINMENT_TRIGGERED = "containment_triggered"
    COMPLIANCE_VIOLATION = "compliance_violation"
    
    # Plugin/KA Events
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_ACTIVATED = "plugin_activated"
    PLUGIN_DEACTIVATED = "plugin_deactivated"
    
    # Client Events
    JOIN_SESSION = "join_session"
    LEAVE_SESSION = "leave_session"
    HEARTBEAT = "heartbeat"

class WebSocketMessage(BaseModel):
    """Standard WebSocket message format"""
    type: MessageType
    session_id: str
    timestamp: datetime
    data: Dict[str, Any]
    message_id: str = None
    
    def __init__(self, **data):
        if not data.get('message_id'):
            data['message_id'] = str(uuid.uuid4())
        if not data.get('timestamp'):
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)

class ConnectionInfo(BaseModel):
    """Information about a WebSocket connection"""
    websocket: WebSocket
    client_id: str
    session_id: str
    connected_at: datetime
    last_heartbeat: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True

class WebSocketManager:
    """
    Manages WebSocket connections for the UKG/USKD simulation system.
    Supports room-based messaging per simulation session.
    """
    
    def __init__(self):
        # Active connections: client_id -> ConnectionInfo
        self.connections: Dict[str, ConnectionInfo] = {}
        
        # Session rooms: session_id -> Set[client_id]
        self.session_rooms: Dict[str, Set[str]] = {}
        
        # Connection locks for thread safety
        self._connection_lock = asyncio.Lock()
        
        logger.info("WebSocket Manager initialized")

    async def connect(self, websocket: WebSocket, client_id: str, session_id: str) -> bool:
        """Accept a new WebSocket connection and add to session room"""
        try:
            await websocket.accept()
            
            async with self._connection_lock:
                # Create connection info
                connection_info = ConnectionInfo(
                    websocket=websocket,
                    client_id=client_id,
                    session_id=session_id,
                    connected_at=datetime.utcnow()
                )
                
                # Add to connections
                self.connections[client_id] = connection_info
                
                # Add to session room
                if session_id not in self.session_rooms:
                    self.session_rooms[session_id] = set()
                self.session_rooms[session_id].add(client_id)
            
            logger.info(f"Client {client_id} connected to session {session_id}")
            
            # Notify other clients in session
            await self.broadcast_to_session(
                session_id=session_id,
                message_type=MessageType.JOIN_SESSION,
                data={"client_id": client_id, "session_id": session_id},
                exclude_client=client_id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect client {client_id}: {e}")
            return False

    async def disconnect(self, client_id: str):
        """Disconnect a WebSocket connection and remove from rooms"""
        async with self._connection_lock:
            if client_id not in self.connections:
                return
            
            connection_info = self.connections[client_id]
            session_id = connection_info.session_id
            
            # Remove from connections
            del self.connections[client_id]
            
            # Remove from session room
            if session_id in self.session_rooms:
                self.session_rooms[session_id].discard(client_id)
                
                # Clean up empty session room
                if not self.session_rooms[session_id]:
                    del self.session_rooms[session_id]
        
        logger.info(f"Client {client_id} disconnected from session {session_id}")
        
        # Notify other clients in session
        await self.broadcast_to_session(
            session_id=session_id,
            message_type=MessageType.LEAVE_SESSION,
            data={"client_id": client_id, "session_id": session_id}
        )

    async def send_to_client(self, client_id: str, message: WebSocketMessage):
        """Send a message to a specific client"""
        if client_id not in self.connections:
            logger.warning(f"Client {client_id} not found")
            return False
        
        try:
            websocket = self.connections[client_id].websocket
            await websocket.send_text(message.model_dump_json())
            return True
        except Exception as e:
            logger.error(f"Failed to send message to client {client_id}: {e}")
            await self.disconnect(client_id)
            return False

    async def broadcast_to_session(
        self, 
        session_id: str, 
        message_type: MessageType, 
        data: Dict[str, Any],
        exclude_client: Optional[str] = None
    ):
        """Broadcast a message to all clients in a session"""
        if session_id not in self.session_rooms:
            logger.warning(f"Session {session_id} has no active connections")
            return
        
        message = WebSocketMessage(
            type=message_type,
            session_id=session_id,
            data=data
        )
        
        # Get clients in session (excluding specified client)
        clients = self.session_rooms[session_id].copy()
        if exclude_client:
            clients.discard(exclude_client)
        
        # Send to all clients in parallel
        tasks = []
        for client_id in clients:
            tasks.append(self.send_to_client(client_id, message))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful = sum(1 for r in results if r is True)
            logger.info(f"Broadcast to session {session_id}: {successful}/{len(tasks)} clients reached")

    async def broadcast_to_all(self, message_type: MessageType, data: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        message = WebSocketMessage(
            type=message_type,
            session_id="*",
            data=data
        )
        
        tasks = []
        for client_id in self.connections.keys():
            tasks.append(self.send_to_client(client_id, message))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful = sum(1 for r in results if r is True)
            logger.info(f"Global broadcast: {successful}/{len(tasks)} clients reached")

    # Simulation Event Methods
    async def notify_simulation_started(self, session_id: str, simulation_data: Dict[str, Any]):
        """Notify clients that a simulation has started"""
        await self.broadcast_to_session(
            session_id=session_id,
            message_type=MessageType.SIMULATION_STARTED,
            data=simulation_data
        )

    async def notify_simulation_completed(self, session_id: str, results: Dict[str, Any]):
        """Notify clients that a simulation has completed"""
        await self.broadcast_to_session(
            session_id=session_id,
            message_type=MessageType.SIMULATION_COMPLETED,
            data=results
        )

    async def notify_layer_started(self, session_id: str, layer_info: Dict[str, Any]):
        """Notify clients that a layer has started processing"""
        await self.broadcast_to_session(
            session_id=session_id,
            message_type=MessageType.LAYER_STARTED,
            data=layer_info
        )

    async def notify_layer_completed(self, session_id: str, layer_result: Dict[str, Any]):
        """Notify clients that a layer has completed"""
        await self.broadcast_to_session(
            session_id=session_id,
            message_type=MessageType.LAYER_COMPLETED,
            data=layer_result
        )

    async def notify_layer_escalated(self, session_id: str, escalation_info: Dict[str, Any]):
        """Notify clients that a layer has escalated"""
        await self.broadcast_to_session(
            session_id=session_id,
            message_type=MessageType.LAYER_ESCALATED,
            data=escalation_info
        )

    async def notify_agent_spawned(self, session_id: str, agent_info: Dict[str, Any]):
        """Notify clients that an agent has been spawned"""
        await self.broadcast_to_session(
            session_id=session_id,
            message_type=MessageType.AGENT_SPAWNED,
            data=agent_info
        )

    async def notify_agent_action(self, session_id: str, action_info: Dict[str, Any]):
        """Notify clients of an agent action"""
        await self.broadcast_to_session(
            session_id=session_id,
            message_type=MessageType.AGENT_ACTION,
            data=action_info
        )

    async def notify_memory_patched(self, session_id: str, patch_info: Dict[str, Any]):
        """Notify clients of a memory patch"""
        await self.broadcast_to_session(
            session_id=session_id,
            message_type=MessageType.MEMORY_PATCHED,
            data=patch_info
        )

    async def notify_memory_forked(self, session_id: str, fork_info: Dict[str, Any]):
        """Notify clients of a memory fork"""
        await self.broadcast_to_session(
            session_id=session_id,
            message_type=MessageType.MEMORY_FORKED,
            data=fork_info
        )

    async def stream_trace_log(self, session_id: str, trace_entry: Dict[str, Any]):
        """Stream a trace log entry to clients"""
        await self.broadcast_to_session(
            session_id=session_id,
            message_type=MessageType.TRACE_LOG,
            data=trace_entry
        )

    async def notify_audit_event(self, session_id: str, audit_info: Dict[str, Any]):
        """Notify clients of an audit event"""
        await self.broadcast_to_session(
            session_id=session_id,
            message_type=MessageType.AUDIT_EVENT,
            data=audit_info
        )

    async def notify_containment_triggered(self, session_id: str, containment_info: Dict[str, Any]):
        """Notify clients that containment has been triggered"""
        await self.broadcast_to_session(
            session_id=session_id,
            message_type=MessageType.CONTAINMENT_TRIGGERED,
            data=containment_info
        )

    async def notify_compliance_violation(self, session_id: str, violation_info: Dict[str, Any]):
        """Notify clients of a compliance violation"""
        await self.broadcast_to_session(
            session_id=session_id,
            message_type=MessageType.COMPLIANCE_VIOLATION,
            data=violation_info
        )

    async def handle_client_message(self, client_id: str, message_data: Dict[str, Any]):
        """Handle incoming message from client"""
        try:
            message_type = message_data.get('type')
            
            if message_type == MessageType.HEARTBEAT:
                # Update last heartbeat
                if client_id in self.connections:
                    self.connections[client_id].last_heartbeat = datetime.utcnow()
                    # Send heartbeat response
                    response = WebSocketMessage(
                        type=MessageType.HEARTBEAT,
                        session_id=self.connections[client_id].session_id,
                        data={"status": "alive"}
                    )
                    await self.send_to_client(client_id, response)
            
            # Add more client message handlers as needed
            
        except Exception as e:
            logger.error(f"Error handling client message from {client_id}: {e}")

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about active sessions and connections"""
        return {
            "total_connections": len(self.connections),
            "active_sessions": len(self.session_rooms),
            "sessions": {
                session_id: len(clients) 
                for session_id, clients in self.session_rooms.items()
            }
        }

    async def cleanup_stale_connections(self, max_age_minutes: int = 30):
        """Clean up stale connections that haven't sent heartbeat"""
        current_time = datetime.utcnow()
        stale_clients = []
        
        for client_id, connection_info in self.connections.items():
            if connection_info.last_heartbeat:
                time_diff = (current_time - connection_info.last_heartbeat).total_seconds() / 60
                if time_diff > max_age_minutes:
                    stale_clients.append(client_id)
        
        for client_id in stale_clients:
            logger.info(f"Cleaning up stale connection: {client_id}")
            await self.disconnect(client_id)

# Singleton instance
websocket_manager = WebSocketManager()

# Export the singleton instance for use in main.py
__all__ = ['WebSocketManager', 'websocket_manager', 'MessageType', 'WebSocketMessage']
