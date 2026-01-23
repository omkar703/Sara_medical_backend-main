"""WebSocket Endpoint for Real-time Signaling"""

from collections import defaultdict
from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.deps import get_current_active_user_ws
from app.models.user import User

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        # connections[organization_id][user_id] = [WebSocket, ...]
        self.active_connections: Dict[UUID, Dict[UUID, List[WebSocket]]] = defaultdict(lambda: defaultdict(list))
        
    async def connect(self, websocket: WebSocket, organization_id: UUID, user_id: UUID):
        await websocket.accept()
        self.active_connections[organization_id][user_id].append(websocket)
        
    def disconnect(self, websocket: WebSocket, organization_id: UUID, user_id: UUID):
        if organization_id in self.active_connections:
            if user_id in self.active_connections[organization_id]:
                if websocket in self.active_connections[organization_id][user_id]:
                    self.active_connections[organization_id][user_id].remove(websocket)
                if not self.active_connections[organization_id][user_id]:
                    del self.active_connections[organization_id][user_id]
            if not self.active_connections[organization_id]:
                del self.active_connections[organization_id]
                
    async def send_personal_message(self, message: dict, organization_id: UUID, user_id: UUID):
        """Send message to a specific user in an organization"""
        if organization_id in self.active_connections and user_id in self.active_connections[organization_id]:
            for connection in self.active_connections[organization_id][user_id]:
                await connection.send_json(message)
                
    async def broadcast_to_org(self, message: dict, organization_id: UUID):
        """Broadcast message to all users in an organization"""
        if organization_id in self.active_connections:
            for user_ws_list in self.active_connections[organization_id].values():
                for connection in user_ws_list:
                    await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str
):
    """
    WebSocket endpoint for real-time updates.
    Authentication via token query parameter.
    """
    try:
        # Authenticate user from token
        user = await get_current_active_user_ws(token)
        if not user:
            await websocket.close(code=4001)
            return

        organization_id = user.organization_id
        user_id = user.id
        
        await manager.connect(websocket, organization_id, user_id)
        
        try:
            while True:
                # Keep alive and simple echo/ping
                data = await websocket.receive_json()
                
                # Handle simple signaling (e.g. "I am typing")
                # For now, just echo or handle specific types
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
        except WebSocketDisconnect:
            manager.disconnect(websocket, organization_id, user_id)
            
    except Exception as e:
        print(f"WebSocket Error: {e}")
        # Try to close if not already closed
        try:
            await websocket.close(code=4000)
        except:
            pass
