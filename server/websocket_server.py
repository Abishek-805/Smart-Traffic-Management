"""
FastAPI application hosting the WebSocket endpoint (/ws/camera) for camera node communication.
"""

from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from server.message_handler import MessageHandler
from ai.utils.logger import get_logger

logger = get_logger("WebSocketServer")

# FastAPI App Instance
app = FastAPI(
    title="Smart Traffic Management Communication Server",
    description="Communication server handling WebSocket node registration, sessions, and heartbeats.",
    version="1.0.0",
)

# Global MessageHandler instance (managers are patched at startup via web/app.py lifespan)
message_handler = MessageHandler()


@app.websocket("/ws/camera")
async def camera_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for camera nodes:
    Accepts connections, receives JSON packets, and routes them to MessageHandler.
    """
    await websocket.accept()
    logger.info(f"Incoming WebSocket connection accepted from client '{websocket.client}'.")
    registered_node_id: Optional[str] = None

    try:
        while True:
            try:
                raw_data = await websocket.receive_json()
                response = await message_handler.process_message(raw_data, websocket)

                # Record registered node ID for disconnect handling
                if (
                    response
                    and response.get("message_type") == "REGISTRATION_ACK"
                    and "payload" in response
                ):
                    registered_node_id = response["payload"].get("node_id")

                # Transmit response packet if applicable
                if response:
                    await websocket.send_json(response)

                    # Send START_STREAM packet automatically upon successful camera registration
                    if (
                        response.get("type") == "REGISTRATION_ACK"
                        or response.get("message_type") == "REGISTRATION_ACK"
                    ):
                        import time
                        start_stream_packet = {
                            "protocol_version": "1.0",
                            "type": "START_STREAM",
                            "message_type": "START_STREAM",
                            "timestamp": time.time(),
                            "payload": {
                                "target_fps": 30,
                                "resolution": "1280x720",
                                "quality": 80,
                            },
                        }
                        await websocket.send_json(start_stream_packet)
                        logger.info(f"Sent START_STREAM command to camera node '{registered_node_id}'.")
            except WebSocketDisconnect:
                raise
            except Exception as frame_err:
                from core.application_context import ApplicationContext
                ApplicationContext.get_instance().frame_processing_errors += 1
                logger.warning(f"Recoverable frame processing error for node '{registered_node_id}': {frame_err}")
                continue

    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed for client '{websocket.client}'.")
        if registered_node_id:
            logger.info(f"Cleaning up disconnected node '{registered_node_id}'.")
            message_handler.handle_connection_loss(registered_node_id)
            await message_handler.connection_manager.disconnect(registered_node_id)
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket loop: {e}", exc_info=True)
        if registered_node_id:
            message_handler.handle_connection_loss(registered_node_id)
            await message_handler.connection_manager.disconnect(registered_node_id)


def get_app() -> FastAPI:
    """Return FastAPI application instance."""
    return app
