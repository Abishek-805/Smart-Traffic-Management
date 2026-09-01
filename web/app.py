"""Combined local deployment: the same REST API and camera runtime in one process."""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from web.routes import dashboard_router, api_router
from server.websocket_server import camera_websocket_endpoint, message_handler
from server.runtime import start_runtime, stop_runtime, telemetry_websocket_endpoint

@asynccontextmanager
async def lifespan(app):
    import os
    os.environ.setdefault("CAMERA_WS_PORT", "8000")
    task = await start_runtime(message_handler)
    try:
        yield
    finally:
        await stop_runtime(task, message_handler)

app = FastAPI(title="Smart Traffic Control Center", version="2.0.0", lifespan=lifespan)
app.include_router(api_router)
app.include_router(dashboard_router)
assets = Path(__file__).resolve().parents[1] / "web-ui" / "dist" / "assets"
if assets.exists():
    app.mount("/assets", StaticFiles(directory=assets), name="assets")
app.add_api_websocket_route("/ws/camera", camera_websocket_endpoint)
app.add_api_websocket_route("/ws/telemetry", telemetry_websocket_endpoint)

@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def legacy_api_redirect(path: str, request: Request):
    # Known v1 routes are matched before this compatibility handler.  Reject
    # unknown canonical routes here so they cannot become /api/v1/v1/... loops.
    if path == "v1" or path.startswith("v1/"):
        raise HTTPException(status_code=404, detail="API route not found")
    return RedirectResponse("/api/v1/" + path + ("?" + request.url.query if request.url.query else ""), status_code=308)

def get_app():
    return app
