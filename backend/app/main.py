"""SANJEEVNI Backend Application Entry Point.

FastAPI application factory with modular routing, centralized error handling,
OpenAPI schema documentation, CORS, and lifespan management.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import (
    SanjeevniException,
    sanjeevni_exception_handler,
    generic_exception_handler,
)
from app.db.database import engine, Base
from app.ml.model_loader import model_loader
from app.realtime.manager import ws_manager

# Import API routers
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.devices import router as devices_router
from app.api.routes.sensors import router as sensors_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.stress import router as stress_router
from app.api.routes.history import router as history_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown routines."""
    # --- Startup ---
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")

    # Create tables if not present
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema verified and synchronized.")
    except Exception as exc:
        logger.error(f"Failed to synchronize database schema: {exc}")

    # Attempt to load the stress ML model
    model_loader.load()

    yield

    # --- Shutdown ---
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")


def create_application() -> FastAPI:
    """Builds and configures the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=(
            "Production-Grade Backend Foundation for SANJEEVNI — "
            "an ESP32 wearable-powered wellness platform. "
            "Enforces an absolute NO-MOCK-DATA policy; returns explicit "
            "machine-readable states when sensor data or ML model is unavailable."
        ),
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # --- CORS Configuration ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Centralized Error Handlers ---
    app.add_exception_handler(SanjeevniException, sanjeevni_exception_handler)
    # Don't catch all in development so test assertions are visible
    if settings.ENVIRONMENT == "production":
        app.add_exception_handler(Exception, generic_exception_handler)

    # --- Root / Health Routes (no version prefix) ---
    app.include_router(health_router)

    # --- Application API v1 Routers ---
    api_v1_prefix = settings.API_V1_STR
    app.include_router(auth_router, prefix=api_v1_prefix)
    app.include_router(users_router, prefix=api_v1_prefix)
    app.include_router(devices_router, prefix=api_v1_prefix)
    app.include_router(sensors_router, prefix=api_v1_prefix)
    app.include_router(dashboard_router, prefix=api_v1_prefix)
    app.include_router(stress_router, prefix=api_v1_prefix)
    app.include_router(history_router, prefix=api_v1_prefix)

    # --- Real-Time WebSocket Telemetry Endpoint ---
    @app.websocket("/ws/{device_id}")
    async def websocket_device_stream(websocket: WebSocket, device_id: str):
        await ws_manager.connect(websocket, device_id)
        try:
            while True:
                # Keepalive loop
                await websocket.receive_text()
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket, device_id)

    # Root route for instant health check
    @app.get("/", tags=["Health"])
    def root():
        return {
            "app": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs": "/docs",
            "health_live": "/health/live",
            "health_ready": "/health/ready",
            "api_v1": settings.API_V1_STR,
        }

    return app


app = create_application()
