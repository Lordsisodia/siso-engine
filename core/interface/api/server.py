"""
Black Box 5 Engine - API Server

FastAPI server with lifespan events for proper service lifecycle management.
Provides REST API and WebSocket endpoints for engine communication.
"""

from contextlib import asynccontextmanager
from typing import Optional
import asyncio
import logging

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add engine to path
from pathlib import Path
engine_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(engine_root))

from infrastructure.kernel import kernel, SystemStatus, RunLevel
from infrastructure.config import ConfigManager
from infrastructure.health import HealthMonitor
from infrastructure.registry import ServiceRegistry
from infrastructure.lifecycle import LifecycleManager


logger = logging.getLogger("APIServer")


# Global instances
health_monitor: Optional[HealthMonitor] = None
service_registry: Optional[ServiceRegistry] = None
lifecycle: Optional[LifecycleManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI.

    Manages service startup and shutdown with proper cleanup.
    """
    global health_monitor, service_registry, lifecycle

    logger.info("🌐 API Server starting...")

    # Startup
    try:
        # Load configuration
        config = ConfigManager.load()

        # Initialize core systems
        from infrastructure.boot_enhanced import initialize_core_systems, start_engine
        boot_config = await initialize_core_systems(config)

        health_monitor = boot_config.health_monitor
        service_registry = boot_config.registry
        lifecycle = boot_config.lifecycle

        # Start engine
        await start_engine(boot_config)

        logger.info("✅ API Server startup complete")

        # Signal ready
        kernel._status = SystemStatus.READY

        yield  # Server is now running

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise

    # Shutdown
    logger.info("🛑 API Server shutting down...")

    try:
        # Shutdown engine
        if lifecycle:
            from core.boot_enhanced import shutdown_engine

            boot_config = type('BootConfig', (), {
                'lifecycle': lifecycle,
                'health_monitor': health_monitor,
                'registry': service_registry,
                'config': config,
                'kernel': kernel
            })()

            await shutdown_engine(boot_config)

        logger.info("✅ API Server shutdown complete")

    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}", exc_info=True)


# Create FastAPI app with lifespan
app = FastAPI(
    title="Black Box 5 Engine",
    description="AI-driven development engine with BMAD and GSD methodologies",
    version="5.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Dependencies
# ============================================================================

async def get_kernel():
    """Get engine kernel instance"""
    return kernel


async def get_health_monitor():
    """Get health monitor instance"""
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitor not initialized")
    return health_monitor


async def get_service_registry():
    """Get service registry instance"""
    if not service_registry:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    return service_registry


# ============================================================================
# Status & Health Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Black Box 5 Engine",
        "version": "5.0.0",
        "status": kernel.status.value,
        "documentation": "/docs"
    }


@app.get("/status")
async def get_status(knl=Depends(get_kernel)):
    """Get engine status"""
    return {
        "status": knl.status.value,
        "run_level": knl.run_level.name,
        "services": list(knl.services.keys()),
        "startup_time": knl._startup_time.isoformat() if knl._startup_time else None
    }


@app.get("/health")
async def health_check(hm=Depends(get_health_monitor)):
    """Basic health check"""
    health = hm.get_current_health()
    return JSONResponse(
        status_code=200 if health["status"] == "healthy" else 503,
        content=health
    )


@app.get("/health/detailed")
async def detailed_health_check(hm=Depends(get_health_monitor)):
    """Detailed health check with service status"""
    return hm.get_current_health()


@app.get("/health/history")
async def health_history(
    hm=Depends(get_health_monitor),
    limit: int = 100
):
    """Get health check history"""
    return hm.get_health_history(limit=limit)


@app.get("/health/uptime")
async def uptime_stats(hm=Depends(get_health_monitor)):
    """Get uptime statistics"""
    return hm.get_uptime()


# ============================================================================
# Service Endpoints
# ============================================================================

@app.get("/services")
async def list_services(registry=Depends(get_service_registry)):
    """List all registered services"""
    return registry.health_status()


@app.get("/services/{service_name}")
async def get_service_status(
    service_name: str,
    registry=Depends(get_service_registry)
):
    """Get status of a specific service"""
    status = registry.health_status(service_name)

    if status.get("status") == "not_found":
        raise HTTPException(status_code=404, detail=f"Service not found: {service_name}")

    return status


# ============================================================================
# Config Endpoints
# ============================================================================

@app.get("/config")
async def get_config():
    """Get current configuration"""
    try:
        config = ConfigManager.load()
        return {
            "source": config.source,
            "validated": config.validated,
            "data": config.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load config: {str(e)}")


@app.post("/config/reload")
async def reload_config():
    """Reload configuration"""
    try:
        config = ConfigManager.reload()
        return {
            "message": "Configuration reloaded",
            "source": config.source
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload config: {str(e)}")


# ============================================================================
# Engine Control Endpoints
# ============================================================================

@app.post("/engine/shutdown")
async def shutdown_engine():
    """Initiate graceful shutdown"""
    if lifecycle:
        # Trigger shutdown event
        lifecycle._shutdown_event.set()
        return {"message": "Shutdown initiated"}
    else:
        raise HTTPException(status_code=503, detail="Lifecycle manager not available")


# ============================================================================
# WebSocket Support (placeholder)
# ============================================================================

# TODO: Implement WebSocket endpoints for real-time updates
# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     try:
#         while True:
#             # Send updates
#             await websocket.send_json({
#                 "status": kernel.status.value,
#                 "health": health_monitor.get_current_health() if health_monitor else {}
#             })
#             await asyncio.sleep(1)
#     except WebSocketDisconnect:
#         logger.info("WebSocket disconnected")


# ============================================================================
# Run Server
# ============================================================================

def run_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = False,
    log_level: str = "info"
):
    """
    Run the API server.

    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload
        log_level: Log level
    """
    uvicorn.run(
        "engine.api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Black Box 5 Engine API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")

    args = parser.parse_args()

    run_server(
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )
