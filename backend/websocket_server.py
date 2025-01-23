from typing import Any, Dict, List

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware


class WebSocketManager:
    def __init__(self):
        self.app = FastAPI()
        self.connected_clients: List[WebSocket] = []
        self._setup_cors()
        self._setup_websocket_endpoint()

    def _setup_cors(self):
        # Update CORS settings to be more permissive for development
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allows all origins
            allow_credentials=True,
            allow_methods=["*"],  # Allows all methods
            allow_headers=["*"],  # Allows all headers
        )

    def _setup_websocket_endpoint(self):
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            print("New client connecting...")
            await websocket.accept()
            print("Client connected successfully")
            self.connected_clients.append(websocket)
            try:
                while True:
                    # Keep connection alive and wait for any client messages
                    data = await websocket.receive_text()
                    print(f"Received message from client: {data}")
            except Exception as e:
                print(f"WebSocket Error: {e}")
            finally:
                print("Client disconnected")
                if websocket in self.connected_clients:
                    self.connected_clients.remove(websocket)

    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        print(
            f"Broadcasting message to {len(self.connected_clients)} clients: {message}"
        )
        disconnected_clients = []
        for client in self.connected_clients:
            try:
                await client.send_json(message)
            except Exception as e:
                print(f"Error sending to client: {e}")
                disconnected_clients.append(client)

        # Clean up disconnected clients
        for client in disconnected_clients:
            if client in self.connected_clients:
                self.connected_clients.remove(client)

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the WebSocket server"""
        import uvicorn

        print(f"Starting WebSocket server on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)


# Example usage:
# ws_manager = WebSocketManager()
# await ws_manager.broadcast_message({
#     "timestamp": datetime.now().isoformat(),
#     "type": "update",
#     "message": "Hello World"
# })
