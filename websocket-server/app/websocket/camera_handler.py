import asyncio
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect
from server.message_handler import MessageHandler
from core.application_context import ApplicationContext
from ai.utils.logger import get_logger

logger = get_logger("CameraWebSocketHandler")

message_handler = MessageHandler()

async def camera_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"Incoming camera WebSocket connection accepted from client '{websocket.client}'.")
    registered_node_id: Optional[str] = None

    try:
        while True:
            try:
                raw_data = await websocket.receive_json()
                response = await message_handler.process_message(raw_data, websocket)

                if response and response.get("message_type") == "REGISTRATION_ACK" and "payload" in response:
                    registered_node_id = response["payload"].get("node_id")

                if response:
                    await websocket.send_json(response)

            except WebSocketDisconnect:
                raise
            except Exception as frame_err:
                ApplicationContext.get_instance().frame_processing_errors += 1
                logger.warning(f"Recoverable frame processing error for node '{registered_node_id}': {frame_err}")
                continue

    except WebSocketDisconnect:
        logger.info(f"Camera WebSocket connection closed for client '{websocket.client}'.")
        if registered_node_id:
            logger.info(f"Cleaning up disconnected node '{registered_node_id}'.")
            message_handler.handle_connection_loss(registered_node_id)
            await message_handler.connection_manager.disconnect(registered_node_id)
    except Exception as e:
        logger.error(f"Unexpected error in camera WebSocket loop: {e}", exc_info=True)
        if registered_node_id:
            message_handler.handle_connection_loss(registered_node_id)
            await message_handler.connection_manager.disconnect(registered_node_id)
