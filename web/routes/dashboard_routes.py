"""
HTML page rendering routes for the Smart Traffic Management Control Center SPA.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DIST_DIR = BASE_DIR / "web-ui" / "dist"
INDEX_HTML = DIST_DIR / "index.html"

router = APIRouter(tags=["HTML Views"])


@router.get("/", response_class=HTMLResponse)
@router.get("/devices", response_class=HTMLResponse)
@router.get("/analytics", response_class=HTMLResponse)
@router.get("/settings", response_class=HTMLResponse)
@router.get("/logs", response_class=HTMLResponse)
async def serve_spa(request: Request):
    """Serve single-page React application (Vite + TS bundle)."""
    if INDEX_HTML.exists():
        return FileResponse(str(INDEX_HTML))
    
    # Fallback status HTML if SPA dist is not pre-built
    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html>
        <head><title>Smart Traffic Control Center</title></head>
        <body style="font-family: sans-serif; background: #0b0f19; color: #fff; text-align: center; padding-top: 100px;">
            <h2>Smart Traffic Control Center — React SPA Backend Ready</h2>
            <p>To view the full React UI, run <code>npm run dev</code> inside <code>web-ui</code> directory or build production assets with <code>npm run build</code>.</p>
            <p><a href="/api/v1/system/health" style="color: #3b82f6;">Check System Health API (/api/v1/system/health)</a></p>
        </body>
        </html>
        """
    )

