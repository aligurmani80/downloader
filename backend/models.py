from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any

class AnalyzeRequest(BaseModel):
    url: str

class VideoFormatOption(BaseModel):
    format_id: str
    resolution: str
    height: Optional[int] = None
    width: Optional[int] = None
    fps: Optional[float] = None
    ext: str
    filesize_approx: Optional[int] = None
    filesize_str: Optional[str] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    has_audio: bool = True
    note: Optional[str] = None

class AudioFormatOption(BaseModel):
    format_id: str
    ext: str
    abr: Optional[float] = None
    quality_label: str
    filesize_approx: Optional[int] = None
    filesize_str: Optional[str] = None
    acodec: Optional[str] = None

class VideoMetadataResponse(BaseModel):
    id: str
    url: str
    title: str
    thumbnail: Optional[str] = None
    duration: Optional[int] = None
    duration_str: Optional[str] = None
    uploader: Optional[str] = None
    uploader_url: Optional[str] = None
    platform: str
    platform_icon: str
    description: Optional[str] = None
    view_count: Optional[int] = None
    video_formats: List[VideoFormatOption]
    audio_formats: List[AudioFormatOption]
    available_resolutions: List[str]

class DownloadRequest(BaseModel):
    url: str
    format_type: str  # 'video' or 'audio'
    quality: Optional[str] = None  # e.g., '1080p', 'best', '320k'
    format_id: Optional[str] = None
    container: Optional[str] = 'mp4'  # 'mp4', 'webm', 'mp3', 'm4a', 'wav'
    title: Optional[str] = None
    thumbnail: Optional[str] = None

class ProgressResponse(BaseModel):
    task_id: str
    status: str  # 'queued', 'downloading', 'merging', 'converting', 'finished', 'error'
    percent: float
    downloaded_bytes: Optional[int] = 0
    total_bytes: Optional[int] = 0
    speed: Optional[float] = 0
    speed_str: Optional[str] = None
    eta: Optional[int] = None
    eta_str: Optional[str] = None
    filename: Optional[str] = None
    filepath: Optional[str] = None
    download_url: Optional[str] = None
    error: Optional[str] = None
    title: Optional[str] = None
    thumbnail: Optional[str] = None
    resolution: Optional[str] = None
    ext: Optional[str] = None

class HistoryItem(BaseModel):
    id: str
    task_id: str
    title: str
    thumbnail: Optional[str] = None
    platform: Optional[str] = None
    format_type: str
    resolution: Optional[str] = None
    ext: str
    filesize: Optional[int] = None
    filesize_str: Optional[str] = None
    download_date: str
    filename: str
    is_available: bool
    download_url: str
