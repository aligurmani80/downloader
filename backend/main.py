import os
import re
import json
import asyncio
import logging
from typing import Optional, Any
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

from config import (
    DOWNLOADS_DIR,
    FFMPEG_PATH,
    FFPROBE_PATH,
    NODE_PATH,
    get_disk_free_space
)
from format_detector import extract_video_info
from download_manager import download_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ultra8k_api")

app = FastAPI(
    title="Ultra 8K Video Downloader API",
    description="High-performance 8K/4K video format detector, downloader, and stream verifier",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoInfoRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    height: Optional[int] = None
    quality: Optional[str] = None  # e.g. "8k", "4k", "2k", "1080p", "720p", "best"
    format_id: Optional[str] = None
    format_type: Optional[str] = "video"  # "video" or "audio"
    preferred_codec: Optional[str] = "auto"  # auto, av01, vp9, avc1
    container: Optional[str] = "mp4"  # mp4, mkv

def parse_quality_to_height(quality: Optional[str], default_height: Optional[int]) -> Optional[int]:
    if default_height:
        return default_height
    if not quality or quality.lower() in ["best", "highest", "max"]:
        return None  # yt-dlp highest available
    q = quality.lower().replace("p", "")
    if "8k" in q or "4320" in q:
        return 4320
    elif "4k" in q or "2160" in q:
        return 2160
    elif "2k" in q or "1440" in q:
        return 1440
    elif "1080" in q:
        return 1080
    elif "720" in q:
        return 720
    elif "480" in q:
        return 480
    elif "360" in q:
        return 360
    elif "240" in q:
        return 240
    elif "144" in q:
        return 144
    return None

@app.get("/api/health")
def health_check():
    disk = get_disk_free_space()
    import yt_dlp
    return {
        "status": "healthy",
        "healthy": True,
        "yt_dlp_version": yt_dlp.version.__version__,
        "ffmpeg_available": os.path.exists(FFMPEG_PATH),
        "ffprobe_available": os.path.exists(FFPROBE_PATH),
        "node_available": bool(os.path.exists(NODE_PATH) if NODE_PATH else False),
        "disk": disk
    }

@app.post("/api/info")
@app.post("/api/analyze")
def get_video_info(req: VideoInfoRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Video URL is required")
    try:
        data = extract_video_info(url)
        # Return both unwrapped and wrapped as data: data for frontend compatibility
        response_dict = {
            "success": True,
            "data": data,
            **data
        }
        return response_dict
    except Exception as e:
        logger.error(f"Error extracting video info: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/download")
async def start_download(req: DownloadRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Video URL is required")
    
    target_height = parse_quality_to_height(req.quality, req.height)

    try:
        task = await download_manager.create_task(
            url=url,
            height=target_height,
            format_id=req.format_id,
            preferred_codec=req.preferred_codec or "auto",
            container=req.container or "mp4",
            format_type=req.format_type or "video"
        )
        return {
            "success": True,
            "job_id": task.task_id,
            "task_id": task.task_id,
            "status": task.status,
            "message": "Download task successfully queued."
        }
    except Exception as e:
        logger.error(f"Error creating download task: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/progress/{task_id}")
def get_task_progress(task_id: str):
    task = download_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Download task not found")
    return task.to_dict()

@app.get("/api/progress/stream/{task_id}")
async def stream_task_progress(task_id: str):
    task = download_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Download task not found")

    async def event_generator():
        while True:
            current_data = task.to_dict()
            yield f"data: {json.dumps(current_data)}\n\n"
            if current_data["status"] in ["completed", "failed", "cancelled"]:
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/api/cancel/{task_id}")
def cancel_task(task_id: str):
    success = download_manager.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "message": "Task cancelled"}

@app.get("/api/file/{task_id}")
@app.get("/api/preview/{task_id}")
async def serve_downloaded_file(task_id: str, request: Request):
    """
    Serves 4K/8K media with HTTP Range support for smooth chunked download and browser preview.
    """
    task = download_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != "completed" or not task.file_path or not os.path.exists(task.file_path):
        raise HTTPException(status_code=400, detail="File is not ready or has not passed verification.")

    file_path = task.file_path
    file_size = os.path.getsize(file_path)
    filename = task.filename or os.path.basename(file_path)
    safe_filename = re.sub(r'[^\w\-_\. ]', '_', filename)

    media_type = "video/mp4"
    if filename.endswith(".mkv"):
        media_type = "video/x-matroska"
    elif filename.endswith(".mp3"):
        media_type = "audio/mpeg"

    range_header = request.headers.get("Range")
    if range_header:
        bytes_match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if bytes_match:
            start = int(bytes_match.group(1))
            end = int(bytes_match.group(2)) if bytes_match.group(2) else file_size - 1
            start = min(start, file_size - 1)
            end = min(end, file_size - 1)
            chunk_length = end - start + 1

            def iter_chunk():
                with open(file_path, "rb") as f:
                    f.seek(start)
                    bytes_remaining = chunk_length
                    while bytes_remaining > 0:
                        chunk_size = min(bytes_remaining, 1024 * 1024)
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        bytes_remaining -= len(chunk)
                        yield chunk

            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_length),
                "Content-Disposition": f'attachment; filename="{safe_filename}"',
            }
            return StreamingResponse(iter_chunk(), status_code=206, headers=headers, media_type=media_type)

    return FileResponse(
        path=file_path,
        filename=safe_filename,
        media_type=media_type,
        headers={"Accept-Ranges": "bytes"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
