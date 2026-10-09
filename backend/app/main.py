import asyncio
import logging
import time
import shutil
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import DOWNLOADS_DIR, FILE_EXPIRY_SECONDS, CLEANUP_INTERVAL_SECONDS
from app.routes.api import router as api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

async def cleanup_expired_files_loop():
    """
    Periodically checks the downloads folder and cleans up directories
    older than FILE_EXPIRY_SECONDS.
    """
    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            now = time.time()
            if DOWNLOADS_DIR.exists():
                for item in DOWNLOADS_DIR.iterdir():
                    if item.is_dir():
                        mtime = item.stat().st_mtime
                        if now - mtime > FILE_EXPIRY_SECONDS:
                            logger.info(f"Cleaning up expired directory: {item.name}")
                            shutil.rmtree(item, ignore_errors=True)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error during directory cleanup: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up. Launching periodic cleanup task...")
    cleanup_task = asyncio.create_task(cleanup_expired_files_loop())
    yield
    logger.info("Application shutting down. Cancelling cleanup task...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="Universal Video & Audio Downloader API",
    description="Professional, high-performance media downloader supporting YouTube, TikTok, and Instagram with guaranteed H.264/AAC compatibility.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Mount frontend build if it exists
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
