from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket.manager import manager


router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"],
)


@router.websocket("/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
):
    await manager.connect(
        user_id,
        websocket,
    )

    try:
        while True:
            # Keep the connection alive.
            # We don't need messages from the client yet.
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(user_id)