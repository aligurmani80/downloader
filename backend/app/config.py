import os
import shutil
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Security and Limits
MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB
FILE_EXPIRY_SECONDS = 30 * 60  # 30 minutes
CLEANUP_INTERVAL_SECONDS = 5 * 60  # Check every 5 minutes

# FFmpeg and FFprobe binary detection
FFMPEG_PATH = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE_PATH = shutil.which("ffprobe") or "ffprobe"

# Allowed domains / URL patterns
SUPPORTED_PLATFORMS = {
    "youtube": ["youtube.com", "youtu.be", "m.youtube.com", "music.youtube.com"],
    "tiktok": ["tiktok.com", "vm.tiktok.com", "vt.tiktok.com", "m.tiktok.com"],
    "instagram": ["instagram.com", "instagr.am"]
}
