import os
import re
import json
import time
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from app.security import validate_url, sanitize_filename
from app.downloader import fetch_media_info, start_download, get_job, jobs
from app.config import DOWNLOADS_DIR, FFMPEG_PATH, FFPROBE_PATH, get_disk_free_space

router = APIRouter(prefix="/api")

HISTORY_FILE = DOWNLOADS_DIR / "history.json"

def load_history() -> List[Dict[str, Any]]:
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_history(history: List[Dict[str, Any]]) -> None:
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def add_to_history(task_id: str, title: str, url: str, format_type: str, quality: str, thumbnail: Optional[str] = None):
    hist = load_history()
    hist.insert(0, {
        "id": task_id,
        "task_id": task_id,
        "title": title or "Media",
        "url": url,
        "format_type": format_type,
        "quality": quality,
        "thumbnail": thumbnail,
        "timestamp": int(time.time()),
        "download_url": f"/api/file/{task_id}"
    })
    save_history(hist[:50])

class UrlRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    format_type: str = "video"
    quality: Optional[str] = "best"
    height: Optional[int] = None
    format_id: Optional[str] = None
    preferred_codec: Optional[str] = "auto"
    container: Optional[str] = "mp4"
    title: Optional[str] = None
    thumbnail: Optional[str] = None

@router.get("/health")
def health_check():
    ffmpeg_ok = bool(shutil.which(FFMPEG_PATH))
    ffprobe_ok = bool(shutil.which(FFPROBE_PATH))
    disk = get_disk_free_space()
    import yt_dlp
    return {
        "status": "healthy",
        "online": True,
        "healthy": ffmpeg_ok and ffprobe_ok,
        "ffmpeg_available": ffmpeg_ok,
        "ffprobe_available": ffprobe_ok,
        "yt_dlp_version": yt_dlp.version.__version__,
        "disk": disk
    }

@router.post("/info")
@router.post("/analyze")
def analyze_endpoint(req: UrlRequest):
    url = req.url.strip()
    is_valid, err_msg, platform = validate_url(url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err_msg)

    try:
        info = fetch_media_info(url)
        return {
            "success": True,
            "data": info,
            **info
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/download")
def download_endpoint(req: DownloadRequest):
    url = req.url.strip()
    is_valid, err_msg, platform = validate_url(url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err_msg)

    if req.format_type not in ("video", "audio"):
        raise HTTPException(status_code=400, detail="Invalid format_type. Must be 'video' or 'audio'.")

    quality_to_use = req.quality or "best"
    task_id = start_download(
        url=url,
        format_type=req.format_type,
        quality=quality_to_use,
        height=req.height,
        preferred_codec=req.preferred_codec or "auto",
        container=req.container or "mp4",
        format_id=req.format_id
    )

    add_to_history(
        task_id=task_id,
        title=req.title or "Media",
        url=url,
        format_type=req.format_type,
        quality=quality_to_use,
        thumbnail=req.thumbnail
    )

    return {
        "success": True,
        "task_id": task_id,
        "job_id": task_id,
        "status": "pending",
        "message": "Download task queued successfully."
    }

@router.get("/progress/{task_id}")
def progress_endpoint(task_id: str):
    job = get_job(task_id)
    if not job:
        raise HTTPException(status_code=404, detail="Task not found or expired.")
    return job

@router.get("/file/{task_id}")
async def file_endpoint(task_id: str, request: Request):
    """
    Serves completed video with HTTP Range header support for large 4K/8K safe streaming.
    """
    job = get_job(task_id)
    if not job:
        raise HTTPException(status_code=404, detail="Task not found or expired.")

    if job.get("status") not in ("finished", "completed"):
        raise HTTPException(status_code=400, detail="File is not ready yet.")

    file_path_str = job.get("file_path")
    if not file_path_str:
        raise HTTPException(status_code=404, detail="File path missing.")

    file_path = Path(file_path_str)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk.")

    file_size = file_path.stat().st_size
    filename = job.get("filename", file_path.name)
    safe_filename = re.sub(r'[^\w\-_\. ]', '_', filename)

    media_type = "video/mp4" if job.get("format_type") == "video" else "audio/mpeg"
    if filename.endswith(".mkv"):
        media_type = "video/x-matroska"

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
        path=str(file_path),
        filename=safe_filename,
        media_type=media_type,
        headers={"Accept-Ranges": "bytes", "Content-Disposition": f'attachment; filename="{safe_filename}"'}
    )

@router.get("/preview/{task_id}")
def preview_endpoint(task_id: str):
    job = get_job(task_id)
    if not job:
        raise HTTPException(status_code=404, detail="Task not found or expired.")

    if job.get("status") not in ("finished", "completed"):
        raise HTTPException(status_code=400, detail="File is not ready yet.")

    file_path_str = job.get("file_path")
    if not file_path_str:
        raise HTTPException(status_code=404, detail="File path missing.")

    file_path = Path(file_path_str)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk.")

    media_type = "video/mp4" if job.get("format_type") == "video" else "audio/mpeg"
    if file_path.name.endswith(".mkv"):
        media_type = "video/x-matroska"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        headers={"Content-Disposition": 'inline', "Accept-Ranges": "bytes"}
    )

@router.get("/history")
def get_history_endpoint():
    return load_history()

@router.delete("/history/{item_id}")
def delete_history_endpoint(item_id: str):
    hist = load_history()
    hist = [item for item in hist if item.get("id") != item_id and item.get("task_id") != item_id]
    save_history(hist)
    return {"success": True, "message": "Item deleted."}

@router.post("/history/clear")
def clear_history_endpoint():
    save_history([])
    return {"success": True, "message": "History cleared."}

@router.post("/downloads/open-folder")
def open_downloads_folder():
    try:
        if os.name == 'nt':
            os.startfile(str(DOWNLOADS_DIR))
        return {"success": True, "path": str(DOWNLOADS_DIR)}
    except Exception as e:
        return {"success": False, "error": str(e), "path": str(DOWNLOADS_DIR)}
