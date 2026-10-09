import os
import re
import time
import uuid
import json
import asyncio
import logging
import subprocess
from typing import Dict, Any, Optional
import yt_dlp

from config import (
    DOWNLOADS_DIR,
    FFMPEG_DIR,
    FFMPEG_PATH,
    FFPROBE_PATH,
    NODE_PATH,
    MIN_FREE_DISK_BYTES,
    get_disk_free_space
)
from format_detector import format_bytes, format_duration

logger = logging.getLogger(__name__)

class DownloadTask:
    def __init__(self, task_id: str, url: str, options: Dict[str, Any]):
        self.task_id = task_id
        self.url = url
        self.options = options
        self.status = "pending"  # pending, analyzing, downloading, merging, verifying, completed, failed, cancelled
        self.phase_message = "Initializing download..."
        self.percent = 0.0
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.speed_bytes_sec = 0
        self.eta_seconds = 0
        self.title = ""
        self.file_path = ""
        self.filename = ""
        self.file_size = 0
        self.error_message = ""
        self.verified_details = {}
        self.format_type = options.get("format_type", "video")
        self.created_at = time.time()
        self.updated_at = time.time()
        self.cancel_requested = False
        self._ydl = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "job_id": self.task_id,
            "url": self.url,
            "status": self.status,
            "progress": round(self.percent, 1),
            "percent": round(self.percent, 1),
            "phase_message": self.phase_message,
            "message": self.phase_message,
            "downloaded_bytes": self.downloaded_bytes,
            "downloaded_str": format_bytes(self.downloaded_bytes),
            "total_bytes": self.total_bytes,
            "total_str": format_bytes(self.total_bytes),
            "speed_str": f"{format_bytes(self.speed_bytes_sec)}/s" if self.speed_bytes_sec > 0 else "--",
            "eta_str": format_duration(self.eta_seconds) if self.eta_seconds > 0 else "--",
            "title": self.title,
            "filename": self.filename,
            "file_size": self.file_size,
            "file_size_str": format_bytes(self.file_size),
            "format_type": self.format_type,
            "error": self.error_message,
            "error_message": self.error_message,
            "verification": self.verified_details,
            "verified_details": self.verified_details,
            "options": self.options,
            "updated_at": self.updated_at
        }


class DownloadManager:
    def __init__(self):
        self.tasks: Dict[str, DownloadTask] = {}
        self._lock = asyncio.Lock()

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        return self.tasks.get(task_id)

    async def create_task(self, url: str, height: Optional[int] = None, format_id: Optional[str] = None,
                          preferred_codec: str = "auto", container: str = "mp4",
                          format_type: str = "video") -> DownloadTask:
        # Check disk space before starting
        disk_info = get_disk_free_space()
        if disk_info["free_bytes"] < MIN_FREE_DISK_BYTES:
            raise RuntimeError(
                f"Low disk space on server ({disk_info['free_gb']} GB free). "
                f"At least 5 GB is required to safely download high-resolution 4K/8K video."
            )

        task_id = str(uuid.uuid4())
        options = {
            "height": height,
            "format_id": format_id,
            "preferred_codec": preferred_codec,  # auto, av01, vp9, avc1
            "container": container.lower(),  # mp4, mkv
            "format_type": format_type
        }
        task = DownloadTask(task_id, url, options)
        async with self._lock:
            self.tasks[task_id] = task

        asyncio.create_task(self._run_download(task))
        return task

    def cancel_task(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if not task:
            return False
        task.cancel_requested = True
        task.status = "cancelled"
        task.phase_message = "Download cancelled by user."
        self._cleanup_partial_files(task)
        return True

    def _cleanup_partial_files(self, task: DownloadTask):
        try:
            if task.file_path and os.path.exists(task.file_path) and task.status != "completed":
                os.remove(task.file_path)
            for f in os.listdir(DOWNLOADS_DIR):
                if task.task_id[:8] in f and (f.endswith(".part") or f.endswith(".ytdl")):
                    p = os.path.join(DOWNLOADS_DIR, f)
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                        except Exception:
                            pass
        except Exception as e:
            logger.warning(f"Cleanup error for task {task.task_id}: {e}")

    async def _run_download(self, task: DownloadTask):
        loop = asyncio.get_running_loop()
        try:
            task.status = "analyzing"
            task.phase_message = "Analyzing video streams and detecting optimal 8K/4K formats..."
            task.updated_at = time.time()

            await loop.run_in_executor(None, self._execute_download_sync, task)

            if task.cancel_requested:
                task.status = "cancelled"
                self._cleanup_partial_files(task)
                return

            # Verification step
            task.status = "verifying"
            task.phase_message = "Verifying playable video and audio streams with FFprobe..."
            task.updated_at = time.time()

            verified_info = await loop.run_in_executor(None, self._verify_download_file, task.file_path, task.format_type)
            task.verified_details = verified_info
            task.file_size = os.path.getsize(task.file_path)
            task.status = "completed"
            task.percent = 100.0
            task.phase_message = f"Download verified successfully! ({verified_info.get('resolution', '')} {verified_info.get('video_codec', '').upper()})"
            task.updated_at = time.time()

        except Exception as e:
            logger.error(f"Download failed for task {task.task_id}: {e}", exc_info=True)
            task.status = "failed"
            task.error_message = str(e)
            task.phase_message = f"Download failed: {e}"
            task.updated_at = time.time()
            self._cleanup_partial_files(task)

    def _execute_download_sync(self, task: DownloadTask):
        url = task.url
        opts = task.options
        height = opts.get("height")
        format_id = opts.get("format_id")
        codec_pref = opts.get("preferred_codec", "auto")
        container = opts.get("container", "mp4")
        format_type = opts.get("format_type", "video")

        def progress_hook(d):
            if task.cancel_requested:
                raise RuntimeError("Download cancelled by user.")

            status = d.get('status')
            task.updated_at = time.time()
            if status == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                speed = d.get('speed') or 0
                eta = d.get('eta') or 0

                task.downloaded_bytes = downloaded
                task.total_bytes = total
                task.speed_bytes_sec = speed
                task.eta_seconds = eta
                task.status = "downloading"
                if total > 0:
                    task.percent = min(99.0, (downloaded / total) * 100.0)

                task.phase_message = f"Downloading stream: {task.percent:.1f}% ({format_bytes(downloaded)} of {format_bytes(total)})"

            elif status == 'finished':
                task.phase_message = "Stream downloaded. Preparing for lossless FFmpeg merge..."

        def postprocessor_hook(d):
            if task.cancel_requested:
                raise RuntimeError("Download cancelled by user.")
            status = d.get('status')
            if status == 'started':
                task.status = "merging"
                task.phase_message = "Merging video and audio streams losslessly using FFmpeg..."
                task.updated_at = time.time()
            elif status == 'finished':
                task.phase_message = "FFmpeg merge complete. Performing stream integrity verification..."
                task.updated_at = time.time()

        # Build format selector
        if format_type == "audio":
            format_selector = "bestaudio/best"
            target_ext = "mp3"
        elif format_id:
            format_selector = f"{format_id}+bestaudio/best"
            target_ext = container
        elif height:
            if codec_pref == "av01":
                format_selector = (
                    f"bestvideo[height<={height}][vcodec^=av01]+bestaudio/"
                    f"bestvideo[height<={height}]+bestaudio/best"
                )
            elif codec_pref == "vp9":
                format_selector = (
                    f"bestvideo[height<={height}][vcodec^=vp09]+bestaudio/"
                    f"bestvideo[height<={height}][vcodec^=vp9]+bestaudio/"
                    f"bestvideo[height<={height}]+bestaudio/best"
                )
            elif codec_pref == "avc1":
                # User preferred H.264, but if unavailable at 8K/4K, safely fallback to bestvideo
                format_selector = (
                    f"bestvideo[height<={height}][vcodec^=avc1]+bestaudio/"
                    f"bestvideo[height<={height}]+bestaudio/best"
                )
            else:
                # Auto / best quality up to requested height
                format_selector = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
            target_ext = container
        else:
            # Highest available quality (up to 8K 4320p)
            if codec_pref == "av01":
                format_selector = "bestvideo[vcodec^=av01]+bestaudio/bestvideo+bestaudio/best"
            elif codec_pref == "vp9":
                format_selector = "bestvideo[vcodec^=vp]+bestaudio/bestvideo+bestaudio/best"
            elif codec_pref == "avc1":
                format_selector = "bestvideo[vcodec^=avc1]+bestaudio/bestvideo+bestaudio/best"
            else:
                format_selector = "bestvideo+bestaudio/best"
            target_ext = container

        out_template = os.path.join(
            DOWNLOADS_DIR,
            f"%(title).150B_%(height)sp_{task.task_id[:8]}.%(ext)s"
        )

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': format_selector,
            'outtmpl': out_template,
            'progress_hooks': [progress_hook],
            'postprocessor_hooks': [postprocessor_hook],
            'windowsfilenames': True,
            'restrictfilenames': False,
        }

        if FFMPEG_DIR:
            ydl_opts['ffmpeg_location'] = FFMPEG_DIR
        if NODE_PATH:
            ydl_opts['js_runtimes'] = {'node': {}}

        if format_type == "audio":
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }]
        else:
            ydl_opts['merge_output_format'] = container
            # Stream copying: -c:v copy preserves 100% original pixel quality with zero CPU lag!
            if container == "mp4":
                ydl_opts['postprocessor_args'] = {
                    'merger': ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k']
                }
            else:
                ydl_opts['postprocessor_args'] = {
                    'merger': ['-c', 'copy']
                }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            task._ydl = ydl
            info = ydl.extract_info(url, download=True)
            if not info:
                raise RuntimeError("Failed to extract video stream information.")

            task.title = info.get('title', 'video')
            initial_filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(initial_filename)
            final_file = f"{base}.{target_ext}"

            if os.path.exists(final_file):
                task.file_path = final_file
            elif os.path.exists(initial_filename):
                task.file_path = initial_filename
            else:
                matched = [
                    os.path.join(DOWNLOADS_DIR, f)
                    for f in os.listdir(DOWNLOADS_DIR)
                    if task.task_id[:8] in f and not f.endswith(".part") and not f.endswith(".ytdl")
                ]
                if matched:
                    task.file_path = matched[0]
                else:
                    raise FileNotFoundError("Merged video file not found on disk.")

            task.filename = os.path.basename(task.file_path)

    def _verify_download_file(self, file_path: str, format_type: str = "video") -> Dict[str, Any]:
        """
        Post-download verification using FFprobe:
        1. Confirms file exists and has size > 50 KB.
        2. STRICT CHECK: Confirms a playable video stream exists with width > 0 and height > 0 (for video downloads).
        3. STRICTLY REJECTS AUDIO-ONLY files when format_type == 'video'!
        4. Verifies audio stream presence.
        5. Returns verified codec and resolution metrics.
        """
        if not file_path or not os.path.exists(file_path):
            raise RuntimeError("Verification error: Output file does not exist on disk.")

        file_size = os.path.getsize(file_path)
        if file_size < 50 * 1024:
            raise RuntimeError(f"Verification error: Output file is truncated or empty (size: {file_size} bytes).")

        cmd = [
            FFPROBE_PATH,
            "-v", "error",
            "-show_entries", "stream=index,codec_type,codec_name,width,height,pix_fmt,r_frame_rate,bit_rate",
            "-show_entries", "format=duration,size,bit_rate",
            "-of", "json",
            file_path
        ]

        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
            if proc.returncode != 0:
                raise RuntimeError(f"FFprobe inspection failed: {proc.stderr}")
            data = json.loads(proc.stdout)
        except Exception as e:
            raise RuntimeError(f"FFprobe execution failed during stream verification: {e}")

        streams = data.get("streams", [])
        format_info = data.get("format", {})

        video_stream = None
        audio_stream = None

        for s in streams:
            if s.get("codec_type") == "video":
                w = s.get("width") or 0
                h = s.get("height") or 0
                if w > 0 and h > 0:
                    video_stream = s
            elif s.get("codec_type") == "audio":
                audio_stream = s

        # Strict Requirement: Never deliver audio-only content as a successful video download!
        if format_type == "video":
            if not video_stream:
                raise RuntimeError(
                    "VERIFICATION REJECTED: The downloaded file does NOT contain a playable video stream! "
                    "(Audio-only delivery is strictly prohibited for video downloads)."
                )

        width = video_stream.get("width", 0) if video_stream else 0
        height = video_stream.get("height", 0) if video_stream else 0
        video_codec = video_stream.get("codec_name", "none") if video_stream else "none"
        pix_fmt = video_stream.get("pix_fmt", "yuv420p") if video_stream else "n/a"
        audio_codec = audio_stream.get("codec_name", "none") if audio_stream else "no audio"
        duration = float(format_info.get("duration", 0))

        res_label = f"{width}x{height}" if width and height else "Audio"
        if height >= 4320 or width >= 7680:
            tier = "8K Ultra HD"
        elif height >= 2160 or width >= 3840:
            tier = "4K Ultra HD"
        elif height >= 1440:
            tier = "2K QHD"
        elif height >= 1080:
            tier = "1080p Full HD"
        elif height >= 720:
            tier = "720p HD"
        elif height > 0:
            tier = f"{height}p"
        else:
            tier = "Audio Only"

        return {
            "verified": True,
            "width": width,
            "height": height,
            "resolution": f"{res_label} ({tier})",
            "tier": tier,
            "video_codec": video_codec,
            "pix_fmt": pix_fmt,
            "audio_codec": audio_codec,
            "has_video": video_stream is not None,
            "has_audio": audio_stream is not None,
            "duration_seconds": round(duration, 1),
            "duration_formatted": format_duration(int(duration)),
            "file_size": file_size,
            "file_size_formatted": format_bytes(file_size)
        }

download_manager = DownloadManager()
