"""Single camera socket endpoint used by both deployment modes."""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from server.message_handler import MessageHandler
message_handler = MessageHandler()

async def camera_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    node_id = None
    try:
        while True:
            data = await websocket.receive_json()
            response = await message_handler.process_message(data, websocket)
            if response:
                if response.get("type") == "REGISTRATION_ACK":
                    node_id = response["payload"]["node_id"]
                await message_handler.connection_manager.send_json(response, websocket)
    except (WebSocketDisconnect, RuntimeError, ValueError):
        pass
    finally:
        if node_id and hasattr(message_handler, "rtc"):
            await message_handler.rtc.close(node_id, websocket)
        # An older socket must never remove a newly registered replacement.
        if node_id and message_handler.connection_manager.get_connection(node_id) is websocket:
            message_handler.handle_connection_loss(node_id)
            await message_handler.connection_manager.disconnect(node_id)

app = FastAPI(title="Traffic camera protocol server")
app.add_api_websocket_route("/ws/camera", camera_websocket_endpoint)

def get_app():
    return app
