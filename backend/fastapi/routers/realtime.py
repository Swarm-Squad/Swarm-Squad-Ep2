from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..utils import ConnectionManager

router = APIRouter(tags=["realtime"])

# Create a connection manager instance
manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Process the received data
            await manager.broadcast({"client_id": client_id, "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(
            {"client_id": client_id, "data": {"status": "disconnected"}}
        )
