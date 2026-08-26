import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import APP_NAME, VERSION, PORT, REDIS_URL
from app.api.router import router as api_v1_router
from app.services.redis_service import AppBackendRedisService
from ai.utils.logger import get_logger

logger = get_logger("AppBackend")

redis_service = AppBackendRedisService(redis_url=REDIS_URL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {APP_NAME} v{VERSION} on port {PORT}...")
    await redis_service.connect()
    listener_task = asyncio.create_task(redis_service.start_listener())
    yield
    logger.info(f"Shutting down {APP_NAME}...")
    listener_task.cancel()
    await redis_service.close()

app = FastAPI(
    title=APP_NAME,
    description="Dedicated REST API backend for Smart Traffic Management System.",
    version=VERSION,
    lifespan=lifespan,
)

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)

@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def legacy_api_redirect(path: str, request: Request):
    canonical_url = f"/api/v1/{path}"
    if request.url.query:
        canonical_url += f"?{request.url.query}"
    return RedirectResponse(url=canonical_url, status_code=308)

def get_app() -> FastAPI:
    return app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=True)
