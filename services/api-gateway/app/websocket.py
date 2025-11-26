"""WebSocket endpoints for real-time updates"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Dict, List
import asyncio
import json
import structlog

logger = structlog.get_logger()

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, org_id: str):
        """Connect a websocket for an organization"""
        await websocket.accept()

        if org_id not in self.active_connections:
            self.active_connections[org_id] = []

        self.active_connections[org_id].append(websocket)
        logger.info("WebSocket connected", org_id=org_id)

    def disconnect(self, websocket: WebSocket, org_id: str):
        """Disconnect a websocket"""
        if org_id in self.active_connections:
            self.active_connections[org_id].remove(websocket)

            if not self.active_connections[org_id]:
                del self.active_connections[org_id]

        logger.info("WebSocket disconnected", org_id=org_id)

    async def send_to_organization(self, org_id: str, message: dict):
        """Send message to all connections for an organization"""
        if org_id not in self.active_connections:
            return

        disconnected = []

        for connection in self.active_connections[org_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("Error sending message", error=str(e))
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection, org_id)

    async def broadcast(self, message: dict):
        """Broadcast message to all connections"""
        for org_id in list(self.active_connections.keys()):
            await self.send_to_organization(org_id, message)


manager = ConnectionManager()


@router.websocket("/posts")
async def websocket_posts(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint for real-time post updates"""
    # Verify token and get org_id
    from jose import jwt, JWTError
    from app.config import settings

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")

        if not user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return

        # Get organization_id from database
        from app.database import get_db_pool

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            org_id = await conn.fetchval(
                "SELECT organization_id FROM users WHERE id = $1", user_id
            )

        if not org_id:
            await websocket.close(code=1008, reason="User not found")
            return

        org_id = str(org_id)

    except JWTError:
        await websocket.close(code=1008, reason="Invalid token")
        return

    # Connect websocket
    await manager.connect(websocket, org_id)

    try:
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()

            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
            else:
                # Echo back for now
                message = json.loads(data)
                await websocket.send_json(
                    {"type": "echo", "data": message}
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, org_id)
        logger.info("Client disconnected", org_id=org_id)
    except Exception as e:
        logger.error("WebSocket error", error=str(e), exc_info=True)
        manager.disconnect(websocket, org_id)


@router.websocket("/analytics")
async def websocket_analytics(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint for real-time analytics updates"""
    # Similar implementation to websocket_posts
    await websocket.accept()

    try:
        while True:
            await websocket.receive_text()
            # Send periodic analytics updates
            await asyncio.sleep(5)
            await websocket.send_json(
                {
                    "type": "analytics_update",
                    "data": {
                        "timestamp": "2024-01-01T00:00:00Z",
                        "metrics": {},
                    },
                }
            )
    except WebSocketDisconnect:
        pass


# Helper function to notify clients (called from other parts of the app)
async def notify_new_post(org_id: str, post_data: dict):
    """Notify organization about new post"""
    await manager.send_to_organization(
        org_id, {"type": "new_post", "data": post_data}
    )


async def notify_response_generated(org_id: str, response_data: dict):
    """Notify organization about generated response"""
    await manager.send_to_organization(
        org_id, {"type": "response_generated", "data": response_data}
    )
