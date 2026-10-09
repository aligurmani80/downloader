import os
import re
import time
import uuid
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List

import yt_dlp
from app.config import (
    DOWNLOADS_DIR, 
    FFMPEG_PATH, 
    FFPROBE_PATH,
    NODE_PATH,
    MAX_FILE_SIZE_BYTES, 
    MIN_FREE_DISK_BYTES,
    get_disk_free_space
)
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

def format_duration(seconds: Optional[int]) -> str:
    if not seconds:
        return "00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def identify_codec(vcodec: Optional[str]) -> str:
    if not vcodec or vcodec == 'none':
        return 'Unknown'
    v = vcodec.lower()
    if 'av01' in v or 'av1' in v:
        return 'AV1'
    if 'vp9' in v or 'vp09' in v:
        return 'VP9'
    if 'avc1' in v or 'h264' in v:
        return 'H.264'
    if 'hev1' in v or 'hvc1' in v or 'h265' in v:
        return 'HEVC'
    return vcodec.split('.')[0].upper()

def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with jobs_lock:
        return jobs.get(job_id)

def update_job(job_id: str, **kwargs) -> None:
    with jobs_lock:
        if job_id in jobs:
            jobs[job_id].update(kwargs)

def fetch_media_info(url: str) -> Dict[str, Any]:
    """
    Extracts actual video metadata, real available resolutions (144p to 8K),
    and available stream codecs using yt-dlp.
    """
    is_valid, err_msg, platform = validate_url(url)
    if not is_valid:
        raise ValueError(err_msg)

    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'socket_timeout': 20,
    }
    if FFMPEG_PATH:
        ydl_opts['ffmpeg_location'] = os.path.dirname(FFMPEG_PATH) if os.path.isabs(FFMPEG_PATH) else None
    if NODE_PATH:
        ydl_opts['js_runtimes'] = {'node': {}}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise ValueError("Could not extract media information.")
                
            if 'entries' in info and info['entries']:
                info = info['entries'][0]

            raw_formats = info.get('formats', [])
            
            # Detect audio formats
            best_audio_size = 0
            for f in raw_formats:
                if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                    s = f.get('filesize') or f.get('filesize_approx') or 0
                    if s > best_audio_size:
                        best_audio_size = s

            # Group video streams by resolution
            res_groups: Dict[int, Dict[str, Any]] = {}
            all_codecs = set()

            for f in raw_formats:
                vcodec = f.get('vcodec')
                if not vcodec or vcodec == 'none':
                    continue
                height = f.get('height')
                width = f.get('width')
                if not height or not isinstance(height, int) or height < 140:
                    continue

                codec_name = identify_codec(vcodec)
                all_codecs.add(codec_name)

                fps = f.get('fps') or 30
                filesize = f.get('filesize') or f.get('filesize_approx') or 0
                dynamic_range = f.get('dynamic_range') or 'SDR'

                if height not in res_groups:
                    res_groups[height] = {
                        'height': height,
                        'width': width or 0,
                        'max_fps': fps,
                        'dynamic_range': dynamic_range,
                        'codecs': set(),
                        'max_filesize': filesize
                    }
                res_groups[height]['codecs'].add(codec_name)
                if fps > res_groups[height]['max_fps']:
                    res_groups[height]['max_fps'] = fps
                if dynamic_range != 'SDR':
                    res_groups[height]['dynamic_range'] = dynamic_range
                if filesize > res_groups[height]['max_filesize']:
                    res_groups[height]['max_filesize'] = filesize

            # Build cleanly sorted resolutions
            available_resolutions = []
            has_8k = False
            has_4k = False
            has_hdr = False

            for h in sorted(res_groups.keys(), reverse=True):
                grp = res_groups[h]
                if h >= 4320:
                    has_8k = True
                    tier = "8K Ultra HD"
                    res_tag = "4320p"
                elif h >= 2160:
                    has_4k = True
                    tier = "4K Ultra HD"
                    res_tag = "2160p"
                elif h >= 1440:
                    tier = "2K QHD"
                    res_tag = "1440p"
                elif h >= 1080:
                    tier = "Full HD"
                    res_tag = "1080p"
                elif h >= 720:
                    tier = "HD"
                    res_tag = "720p"
                elif h >= 480:
                    tier = "SD"
                    res_tag = "480p"
                elif h >= 360:
                    tier = "Standard"
                    res_tag = "360p"
                elif h >= 240:
                    tier = "Low"
                    res_tag = "240p"
                else:
                    tier = "Ultra Low"
                    res_tag = "144p"

                if grp['dynamic_range'] != 'SDR':
                    has_hdr = True

                est_total = grp['max_filesize'] + best_audio_size if grp['max_filesize'] > 0 else 0
                codec_list = sorted(list(grp['codecs']))

                available_resolutions.append({
                    'height': h,
                    'width': grp['width'],
                    'res_tag': res_tag,
                    'tier_name': tier,
                    'full_label': f"{res_tag} - {tier}",
                    'fps': int(grp['max_fps']),
                    'is_hdr': grp['dynamic_range'] != 'SDR',
                    'dynamic_range': grp['dynamic_range'],
                    'codecs': codec_list,
                    'filesize_bytes': est_total,
                    'filesize_str': format_bytes(est_total),
                    'codec_note': "8K master stream in AV1/VP9 (YouTube standard)." if h >= 4320 else ("H.264 compatible." if "H.264" in codec_list else "AV1/VP9 streaming.")
                })

            duration_sec = info.get('duration') or 0
            duration_str = format_duration(duration_sec)

            # Build quality options for UI
            quality_options = []
            quality_options.append({
                "id": "best",
                "label": f"Maximum Available ({available_resolutions[0]['res_tag'] if available_resolutions else 'Best'})",
                "type": "video",
                "format": "mp4",
                "recommended": True,
                "resolution": "Best",
                "container": "mp4"
            })

            for r in available_resolutions:
                quality_options.append({
                    "id": str(r['height']),
                    "label": r['full_label'],
                    "type": "video",
                    "format": "mp4",
                    "recommended": False,
                    "resolution": f"{r['height']}p",
                    "codecs": r['codecs'],
                    "filesize_str": r['filesize_str']
                })

            quality_options.append({
                "id": "mp3",
                "label": "HQ Audio Only (MP3 320k)",
                "type": "audio",
                "format": "mp3",
                "recommended": False,
                "resolution": "Audio",
                "container": "mp3"
            })

            max_res_label = available_resolutions[0]['full_label'] if available_resolutions else "Best Quality"

            return {
                "title": info.get("title") or "Unknown Video",
                "uploader": info.get("uploader") or info.get("channel") or "Unknown Creator",
                "duration": duration_str,
                "duration_seconds": duration_sec,
                "duration_formatted": duration_str,
                "thumbnail": info.get("thumbnail"),
                "platform": platform.capitalize(),
                "webpage_url": info.get("webpage_url") or url,
                "view_count": info.get("view_count"),
                "has_8k": has_8k,
                "has_4k": has_4k,
                "has_hdr": has_hdr,
                "max_resolution": max_res_label,
                "resolutions": available_resolutions,
                "all_codecs": sorted(list(all_codecs)),
                "qualities": quality_options
            }

    except Exception as e:
        logger.error(f"Failed to fetch media info: {e}", exc_info=True)
        raise ValueError(f"Could not extract video metadata: {str(e)}")

def start_download(url: str, format_type: str = "video", quality: str = "best",
                   height: Optional[int] = None, preferred_codec: str = "auto",
                   container: str = "mp4", format_id: Optional[str] = None) -> str:
    """
    Creates and initiates an asynchronous download worker.
    """
    # Verify free disk space before queueing
    disk_info = get_disk_free_space()
    if disk_info["free_bytes"] < MIN_FREE_DISK_BYTES:
        raise ValueError(f"Insufficient server disk space ({disk_info['free_gb']} GB free). Minimum 5 GB required.")

    job_id = str(uuid.uuid4())
    job_data = {
        "job_id": job_id,
        "task_id": job_id,
        "url": url,
        "format_type": format_type,
        "quality": quality,
        "height": height,
        "preferred_codec": preferred_codec,
        "container": container,
        "format_id": format_id,
        "status": "pending",
        "progress": 0.0,
        "percent": 0.0,
        "downloaded_bytes": 0,
        "downloaded_str": "0 KB",
        "total_bytes": 0,
        "total_str": "0 KB",
        "speed_str": "--",
        "eta_str": "--",
        "message": "Download task queued...",
        "phase_message": "Download task queued...",
        "file_path": None,
        "filename": None,
        "file_size": 0,
        "verification": None,
        "verified_details": None,
        "created_at": time.time(),
        "updated_at": time.time(),
        "error": None,
        "error_message": None
    }

    with jobs_lock:
        jobs[job_id] = job_data

    thread = threading.Thread(
        target=_download_worker,
        args=(job_id, url, format_type, quality, height, preferred_codec, container, format_id),
        daemon=True
    )
    thread.start()
    return job_id

def _download_worker(job_id: str, url: str, format_type: str, quality: str,
                     height: Optional[int], preferred_codec: str, container: str,
                     format_id: Optional[str]) -> None:
    job_dir = DOWNLOADS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    update_job(job_id, status="analyzing", message="Resolving 8K/4K media streams...")

    def progress_hook(d):
        status = d.get('status')
        if status == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes') or 0
            speed = d.get('speed') or 0
            eta = d.get('eta') or 0

            percent = 0.0
            if total > 0:
                percent = min(99.0, (downloaded / total) * 100.0)

            speed_s = f"{format_bytes(speed)}/s" if speed else "--"
            eta_s = format_duration(eta) if eta else "--"

            update_job(
                job_id,
                status="downloading",
                progress=round(percent, 1),
                percent=round(percent, 1),
                downloaded_bytes=downloaded,
                downloaded_str=format_bytes(downloaded),
                total_bytes=total,
                total_str=format_bytes(total),
                speed_str=speed_s,
                eta_str=eta_s,
                message=f"Downloading: {percent:.1f}% ({format_bytes(downloaded)} of {format_bytes(total)})",
                phase_message=f"Downloading: {percent:.1f}% ({format_bytes(downloaded)} of {format_bytes(total)})",
                updated_at=time.time()
            )
        elif status == 'finished':
            update_job(
                job_id,
                status="merging",
                message="Lossless stream muxing with FFmpeg...",
                phase_message="Lossless stream muxing with FFmpeg...",
                updated_at=time.time()
            )

    try:
        is_video = (format_type == "video")
        temp_out_template = str((job_dir / f"stream_{job_id}.%(ext)s").resolve())

        # Determine target height
        q_cleaned = quality.replace("p", "").strip().lower()
        target_h = height
        if not target_h:
            if "8k" in q_cleaned or "4320" in q_cleaned:
                target_h = 4320
            elif "4k" in q_cleaned or "2160" in q_cleaned:
                target_h = 2160
            elif "2k" in q_cleaned or "1440" in q_cleaned:
                target_h = 1440
            elif q_cleaned.isdigit():
                target_h = int(q_cleaned)

        if is_video:
            # Format selector without restricting 8K to H.264
            if format_id:
                format_str = f"{format_id}+bestaudio/best"
            elif target_h:
                if preferred_codec == "av01":
                    format_str = f"bestvideo[height<={target_h}][vcodec^=av01]+bestaudio/bestvideo[height<={target_h}]+bestaudio/best"
                elif preferred_codec == "vp9":
                    format_str = f"bestvideo[height<={target_h}][vcodec^=vp]+bestaudio/bestvideo[height<={target_h}]+bestaudio/best"
                elif preferred_codec == "avc1":
                    format_str = f"bestvideo[height<={target_h}][vcodec^=avc1]+bestaudio/bestvideo[height<={target_h}]+bestaudio/best"
                else:
                    format_str = f"bestvideo[height<={target_h}]+bestaudio/best[height<={target_h}]/best"
            else:
                # Highest available quality (up to 8K)
                if preferred_codec == "av01":
                    format_str = "bestvideo[vcodec^=av01]+bestaudio/bestvideo+bestaudio/best"
                elif preferred_codec == "vp9":
                    format_str = "bestvideo[vcodec^=vp]+bestaudio/bestvideo+bestaudio/best"
                elif preferred_codec == "avc1":
                    format_str = "bestvideo[vcodec^=avc1]+bestaudio/bestvideo+bestaudio/best"
                else:
                    format_str = "bestvideo+bestaudio/best"

            target_container = container.lower() if container else "mp4"

            ydl_opts = {
                'format': format_str,
                'outtmpl': temp_out_template,
                'merge_output_format': target_container,
                'quiet': True,
                'no_warnings': True,
                'max_filesize': MAX_FILE_SIZE_BYTES,
                'progress_hooks': [progress_hook],
                'windowsfilenames': True,
            }

            if FFMPEG_PATH:
                ydl_opts['ffmpeg_location'] = os.path.dirname(FFMPEG_PATH) if os.path.isabs(FFMPEG_PATH) else None
            if NODE_PATH:
                ydl_opts['js_runtimes'] = {'node': {}}

            # Lossless stream copying: preserves 100% video quality without CPU re-compression
            if target_container == "mp4":
                ydl_opts['postprocessor_args'] = {
                    'merger': ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k']
                }
            else:
                ydl_opts['postprocessor_args'] = {
                    'merger': ['-c', 'copy']
                }
        else:
            # Audio MP3 download
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_out_template,
                'quiet': True,
                'no_warnings': True,
                'max_filesize': MAX_FILE_SIZE_BYTES,
                'progress_hooks': [progress_hook],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }]
            }
            if FFMPEG_PATH:
                ydl_opts['ffmpeg_location'] = os.path.dirname(FFMPEG_PATH) if os.path.isabs(FFMPEG_PATH) else None

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(url, download=True)
            raw_title = meta.get("title") or "downloaded_file"

        # Locate output file
        downloaded_candidates = [
            f for f in job_dir.iterdir()
            if f.is_file() and not f.name.endswith(".part") and not f.name.endswith(".ytdl")
        ]
        if not downloaded_candidates:
            raise FileNotFoundError("Merged output file was not found after download.")

        downloaded_file = max(downloaded_candidates, key=lambda f: f.stat().st_size)

        # Verification Step via FFprobe
        update_job(
            job_id,
            status="verifying",
            message="Verifying playable video and audio streams with FFprobe...",
            phase_message="Verifying playable video and audio streams with FFprobe..."
        )

        verification_result = verify_media_file(downloaded_file, expected_type=format_type)

        safe_name = sanitize_filename(raw_title)
        ext = downloaded_file.suffix or (".mp4" if is_video else ".mp3")
        final_filename = f"{safe_name}{ext}"
        final_filepath = job_dir / final_filename

        if final_filepath != downloaded_file:
            if final_filepath.exists():
                final_filepath.unlink()
            downloaded_file.rename(final_filepath)

        final_size = final_filepath.stat().st_size
        verification_result["size_bytes"] = final_size

        update_job(
            job_id,
            status="completed",
            progress=100.0,
            percent=100.0,
            file_path=str(final_filepath.resolve()),
            filename=final_filename,
            file_size=final_size,
            file_size_str=format_bytes(final_size),
            title=raw_title,
            verification=verification_result,
            verified_details=verification_result,
            message=f"Download verified successfully! ({verification_result.get('resolution', '')})",
            phase_message=f"Download verified successfully! ({verification_result.get('resolution', '')})"
        )

    except Exception as e:
        logger.error(f"Download worker error for job {job_id}: {e}", exc_info=True)
        update_job(
            job_id,
            status="failed",
            error=str(e),
            error_message=str(e),
            message=f"Error: {str(e)}",
            phase_message=f"Error: {str(e)}"
        )
        # Clean up partial files
        try:
            for f in job_dir.iterdir():
                if f.name.endswith(".part") or f.name.endswith(".ytdl"):
                    f.unlink()
        except Exception:
            pass
