import os
import json
import time
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.security import validate_url, sanitize_filename
from app.downloader import fetch_media_info, start_download, get_job, jobs
from app.config import DOWNLOADS_DIR, FFMPEG_PATH, FFPROBE_PATH

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
    except Exception as e:
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
    format_id: Optional[str] = None
    container: Optional[str] = "mp4"
    title: Optional[str] = None
    thumbnail: Optional[str] = None

@router.get("/health")
def health_check():
    ffmpeg_ok = bool(shutil.which(FFMPEG_PATH))
    ffprobe_ok = bool(shutil.which(FFPROBE_PATH))
    return {
        "status": "healthy",
        "online": True,
        "healthy": ffmpeg_ok and ffprobe_ok,
        "ffmpeg_available": ffmpeg_ok,
        "ffprobe_available": ffprobe_ok
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
        return info
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
        quality=quality_to_use
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
        "message": "Download task queued successfully."
    }

@router.get("/progress/{task_id}")
def progress_endpoint(task_id: str):
    job = get_job(task_id)
    if not job:
        raise HTTPException(status_code=404, detail="Task not found or expired.")
    return job

@router.get("/file/{task_id}")
def file_endpoint(task_id: str):
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
    filename = job.get("filename", file_path.name)

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
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

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        headers={"Content-Disposition": 'inline'}
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
