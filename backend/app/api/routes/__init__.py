"""Routes package exports."""
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.devices import router as devices_router
from app.api.routes.sensors import router as sensors_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.stress import router as stress_router
from app.api.routes.history import router as history_router

__all__ = [
    "health_router",
    "auth_router",
    "users_router",
    "devices_router",
    "sensors_router",
    "dashboard_router",
    "stress_router",
    "history_router",
]
