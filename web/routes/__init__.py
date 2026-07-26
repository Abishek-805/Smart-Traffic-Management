"""
Routes package for Smart Traffic Management Web Control Center.
"""

from web.routes.dashboard_routes import router as dashboard_router
from web.routes.api_routes import router as api_router

__all__ = ["dashboard_router", "api_router"]
