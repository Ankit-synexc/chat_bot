import logging
import traceback
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from config.database import connect_db, close_db
from ml_core.embedder import embedder
from ml_core.reranker import reranker
from controllers.health_controller import health_check
from services.cache_service import clear_cache
from routers import all_routers

# Setup basic logging
logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Hook ---
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    
    db_connected = False
    try:
        await connect_db()
        db_connected = True
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        
    logger.info("Skipping ML models warmup to save memory on free tier...")
    import torch
    torch.set_num_threads(1)
    models_loaded = False
    
    logger.info(f"Startup complete. DB connected: {db_connected}")
    
    yield
    
    # --- Shutdown Hook ---
    logger.info(f"Shutting down {settings.APP_NAME}...")
    await close_db()
    logger.info("Shutdown complete.")

app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent Document Q&A Platform",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url}")
    # Log traceback internally, NEVER leak to client
    logger.error("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error"}
    )

# Health endpoint (no auth)
@app.get("/health", tags=["health"])
async def health_check_route():
    """Application health endpoint retrieving DB/ML load statuses."""
    return await health_check()

# Cache management (no auth, admin utility)
@app.post("/cache/clear", tags=["admin"])
async def clear_cache_route():
    """Flush the in-memory query cache."""
    clear_cache()
    return {"success": True, "message": "Cache cleared"}

# Debug diagnostic endpoint (no auth)
from controllers.debug_controller import run_diagnostics

@app.get("/debug/check", tags=["debug"])
async def debug_check(question: str = "What does this company do?"):
    """Run full pipeline diagnostics. Pass ?question=your+question to test a specific query."""
    return await run_diagnostics(question)

# Mount all feature routers
for router in all_routers:
    app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
