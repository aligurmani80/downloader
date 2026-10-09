import os
import time
import uuid
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional

import yt_dlp
from app.config import DOWNLOADS_DIR, FFMPEG_PATH, MAX_FILE_SIZE_BYTES
from app.security import sanitize_filename, validate_url
from app.verifier import verify_media_file, ensure_compatible_mp4, VerificationError

logger = logging.getLogger(__name__)

# In-memory job store
jobs_lock = threading.Lock()
jobs: Dict[str, Dict[str, Any]] = {}

def format_bytes(b: Optional[float]) -> str:
    if not b:
        return "0 KB"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if b < 1024.0:
            return f"{b:.1f} {unit}"
        b /= 1024.0
    return f"{b:.1f} TB"

def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with jobs_lock:
        return jobs.get(job_id)

def update_job(job_id: str, **kwargs) -> None:
    with jobs_lock:
        if job_id in jobs:
            jobs[job_id].update(kwargs)

def fetch_media_info(url: str) -> Dict[str, Any]:
    """
    Extracts video metadata and supported formats without downloading.
    """
    is_valid, err_msg, platform = validate_url(url)
    if not is_valid:
        raise ValueError(err_msg)

    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'socket_timeout': 15,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise ValueError("Could not extract media information.")
                
            if 'entries' in info and info['entries']:
                info = info['entries'][0]

            raw_formats = info.get('formats', [])
            available_heights = set()
            for f in raw_formats:
                h = f.get('height')
                if h and isinstance(h, int) and h >= 144:
                    available_heights.add(h)

            sorted_heights = sorted(list(available_heights), reverse=True)
            
            duration_sec = info.get('duration') or 0
            if duration_sec >= 3600:
                hours = int(duration_sec // 3600)
                minutes = int((duration_sec % 3600) // 60)
                seconds = int(duration_sec % 60)
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                minutes = int(duration_sec // 60)
                seconds = int(duration_sec % 60)
                duration_str = f"{minutes:02d}:{seconds:02d}"

            quality_options = []
            standard_resolutions = [1080, 720, 480, 360]
            
            quality_options.append({
                "id": "best",
                "label": "Best Available (Max Quality)",
                "type": "video",
                "format": "mp4",
                "recommended": True,
                "resolution": "Best",
                "container": "mp4"
            })

            for res in standard_resolutions:
                if any(h >= res for h in sorted_heights):
                    quality_options.append({
                        "id": str(res),
                        "label": f"{res}p HD" if res >= 720 else f"{res}p SD",
                        "type": "video",
                        "format": "mp4",
                        "recommended": False,
                        "resolution": f"{res}p",
                        "container": "mp4"
                    })

            quality_options.append({
                "id": "mp3",
                "label": "MP3 Audio Only (320 kbps)",
                "type": "audio",
                "format": "mp3",
                "recommended": False,
                "resolution": "320kbps",
                "container": "mp3"
            })

            video_formats = [q for q in quality_options if q['type'] == 'video']
            audio_formats = [q for q in quality_options if q['type'] == 'audio']

            return {
                "id": info.get("id"),
                "title": info.get("title") or "Untitled Media",
                "thumbnail": info.get("thumbnail"),
                "duration": duration_str,
                "duration_seconds": duration_sec,
                "uploader": info.get("uploader") or info.get("channel") or info.get("creator") or "Unknown Author",
                "platform": platform,
                "webpage_url": info.get("webpage_url") or url,
                "qualities": quality_options,
                "formats": {
                    "video": video_formats,
                    "audio": audio_formats
                }
            }

    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        if "Private video" in msg:
            raise ValueError("This video is private. Please provide a public video URL.")
        elif "Sign in to confirm your age" in msg:
            raise ValueError("This video requires age verification / login on the platform.")
        elif "DRM" in msg:
            raise ValueError("This video is DRM protected and cannot be processed.")
        elif "Video unavailable" in msg:
            raise ValueError("The video is unavailable or has been removed.")
        else:
            clean_msg = msg.split("ERROR:")[-1].strip()
            raise ValueError(f"Platform error: {clean_msg}")
    except Exception as e:
        logger.error(f"Error extracting video info: {e}")
        raise ValueError(f"Failed to fetch video information: {str(e)}")

def run_download_job(job_id: str, url: str, format_type: str, quality: str) -> None:
    """
    Background worker that handles downloading, FFmpeg stream merging,
    transcoding to H.264/AAC, and rigorous ffprobe verification.
    """
    job_dir = DOWNLOADS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    
    update_job(
        job_id,
        status="downloading",
        percent=5.0,
        progress=5.0,
        message="Starting download and resolving streams..."
    )

    def progress_hook(d: Dict[str, Any]):
        if d.get('status') == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes') or 0
            speed = d.get('speed') or 0
            eta = d.get('eta') or 0

            pct = 10.0
            if total > 0:
                pct = 10.0 + (downloaded / total) * 60.0

            speed_str = f"{format_bytes(speed)}/s" if speed else ""
            eta_str = f"{eta}s" if eta else ""

            update_job(
                job_id,
                percent=round(min(pct, 70.0), 1),
                progress=round(min(pct, 70.0), 1),
                speed_str=speed_str,
                eta_str=eta_str,
                message=f"Downloading media stream ({round(pct, 1)}%)..."
            )
        elif d.get('status') == 'finished':
            update_job(
                job_id,
                percent=75.0,
                progress=75.0,
                status="merging",
                message="Download stream completed. Merging audio & video..."
            )

    try:
        is_video = (format_type == "video")
        # Explicit intermediate file name to prevent FFmpeg in-place edit errors
        temp_out_template = str((job_dir / f"stream_in_{job_id}.%(ext)s").resolve())

        q_cleaned = quality.replace("p", "").strip().lower()

        if is_video:
            # Strictly select video + audio, never audio-only
            if q_cleaned == "1080":
                format_str = (
                    "bestvideo[height<=1080][vcodec^=avc1]+bestaudio[acodec^=mp4a]/"
                    "bestvideo[height<=1080]+bestaudio/"
                    "best[height<=1080]/"
                    "bestvideo+bestaudio/best"
                )
            elif q_cleaned == "720":
                format_str = (
                    "bestvideo[height<=720][vcodec^=avc1]+bestaudio[acodec^=mp4a]/"
                    "bestvideo[height<=720]+bestaudio/"
                    "best[height<=720]/"
                    "bestvideo+bestaudio/best"
                )
            elif q_cleaned == "480":
                format_str = (
                    "bestvideo[height<=480][vcodec^=avc1]+bestaudio[acodec^=mp4a]/"
                    "bestvideo[height<=480]+bestaudio/"
                    "best[height<=480]/"
                    "bestvideo+bestaudio/best"
                )
            elif q_cleaned == "360":
                format_str = (
                    "bestvideo[height<=360][vcodec^=avc1]+bestaudio[acodec^=mp4a]/"
                    "bestvideo[height<=360]+bestaudio/"
                    "best[height<=360]/"
                    "bestvideo+bestaudio/best"
                )
            else:  # "best"
                format_str = (
                    "bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]/"
                    "bestvideo+bestaudio/"
                    "best"
                )

            ydl_opts = {
                'format': format_str,
                'outtmpl': temp_out_template,
                'merge_output_format': 'mp4',
                'quiet': True,
                'no_warnings': True,
                'ffmpeg_location': FFMPEG_PATH,
                'max_filesize': MAX_FILE_SIZE_BYTES,
                'progress_hooks': [progress_hook],
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }]
            }
        else:
            # Audio MP3 download
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_out_template,
                'quiet': True,
                'no_warnings': True,
                'ffmpeg_location': FFMPEG_PATH,
                'max_filesize': MAX_FILE_SIZE_BYTES,
                'progress_hooks': [progress_hook],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }]
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(url, download=True)
            raw_title = meta.get("title") or "downloaded_file"

        # Locate the downloaded file in job_dir
        downloaded_files = list(job_dir.glob(f"stream_in_{job_id}.*"))
        if not downloaded_files:
            # fallback to any file not part
            downloaded_files = [f for f in job_dir.glob("*") if not f.name.endswith(".part") and not f.name.endswith(".ytdl")]

        if not downloaded_files:
            raise RuntimeError("No completed media file found after yt-dlp run.")

        raw_file = downloaded_files[0]
        safe_title = sanitize_filename(raw_title)

        if is_video:
            update_job(
                job_id,
                percent=80.0,
                progress=80.0,
                status="converting",
                message="Transcoding to device-compatible H.264/AAC MP4..."
            )
            final_filename = f"{safe_title}.mp4"
            final_path = job_dir / final_filename

            # If input file is different from output, transcode/remux cleanly
            if raw_file.resolve() == final_path.resolve():
                temp_renamed = job_dir / f"temp_{job_id}.mp4"
                raw_file.rename(temp_renamed)
                raw_file = temp_renamed

            ensure_compatible_mp4(raw_file, final_path)
            
            if raw_file.exists():
                try:
                    raw_file.unlink()
                except Exception:
                    pass

            update_job(
                job_id,
                percent=92.0,
                progress=92.0,
                status="converting",
                message="Running ffprobe stream verification (checking video & audio tracks)..."
            )

            verification = verify_media_file(final_path, expected_type="video")

        else:
            update_job(
                job_id,
                percent=85.0,
                progress=85.0,
                status="converting",
                message="Verifying audio stream..."
            )
            final_filename = f"{safe_title}.mp3"
            final_path = job_dir / final_filename
            
            if raw_file.resolve() != final_path.resolve():
                if final_path.exists():
                    final_path.unlink()
                raw_file.rename(final_path)

            verification = verify_media_file(final_path, expected_type="audio")

        # Success!
        update_job(
            job_id,
            status="finished",
            state="completed",
            percent=100.0,
            progress=100.0,
            message="Ready! Video & audio streams verified successfully.",
            file_path=str(final_path),
            filename=final_filename,
            file_size=final_path.stat().st_size,
            file_size_formatted=format_bytes(final_path.stat().st_size),
            download_url=f"/api/file/{job_id}",
            preview_url=f"/api/preview/{job_id}",
            verification=verification
        )

    except VerificationError as ve:
        logger.error(f"Verification error in job {job_id}: {ve}")
        update_job(
            job_id,
            status="error",
            state="failed",
            error=str(ve),
            message="Verification failed: Output file missing required video/audio tracks."
        )
    except Exception as e:
        logger.exception(f"Download job {job_id} failed: {e}")
        update_job(
            job_id,
            status="error",
            state="failed",
            error=str(e),
            message=f"Download failed: {str(e)}"
        )

def start_download(url: str, format_type: str, quality: str) -> str:
    """
    Creates a job and launches the background download thread.
    """
    job_id = str(uuid.uuid4())
    with jobs_lock:
        jobs[job_id] = {
            "job_id": job_id,
            "task_id": job_id,
            "url": url,
            "format_type": format_type,
            "quality": quality,
            "status": "queued",
            "state": "pending",
            "percent": 0.0,
            "progress": 0.0,
            "speed_str": "",
            "eta_str": "",
            "message": "Initializing download task...",
            "created_at": time.time(),
            "download_url": f"/api/file/{job_id}",
            "preview_url": f"/api/preview/{job_id}",
            "error": None
        }

    thread = threading.Thread(
        target=run_download_job,
        args=(job_id, url, format_type, quality),
        daemon=True
    )
    thread.start()
    return job_id
