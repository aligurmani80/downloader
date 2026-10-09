import os
import shutil
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Security and Limits: Support large 4K/8K video downloads (up to 30 GB)
MAX_FILE_SIZE_BYTES = 30 * 1024 * 1024 * 1024  # 30 GB for 8K video support
MIN_FREE_DISK_BYTES = 5 * 1024 * 1024 * 1024   # 5 GB minimum free space
FILE_EXPIRY_SECONDS = 60 * 60  # 1 hour
CLEANUP_INTERVAL_SECONDS = 10 * 60  # Check every 10 minutes

# FFmpeg and FFprobe binary detection
def find_binary(binary_name: str) -> str:
    found = shutil.which(binary_name)
    if found:
        return found
    winget_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
    if os.path.exists(winget_dir):
        for root, dirs, files in os.walk(winget_dir):
            if f"{binary_name}.exe" in files:
                return os.path.join(root, f"{binary_name}.exe")
    return binary_name

FFMPEG_PATH = find_binary("ffmpeg")
FFPROBE_PATH = find_binary("ffprobe")
NODE_PATH = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"

# Allowed domains / URL patterns
SUPPORTED_PLATFORMS = {
    "youtube": ["youtube.com", "youtu.be", "m.youtube.com", "music.youtube.com"],
    "tiktok": ["tiktok.com", "vm.tiktok.com", "vt.tiktok.com", "m.tiktok.com"],
    "instagram": ["instagram.com", "instagr.am"]
}

def get_disk_free_space(path: Path = DOWNLOADS_DIR) -> dict:
    total, used, free = shutil.disk_usage(path)
    return {
        "total_bytes": total,
        "used_bytes": used,
        "free_bytes": free,
        "total_gb": round(total / (1024**3), 2),
        "free_gb": round(free / (1024**3), 2),
        "sufficient_for_8k": free > MIN_FREE_DISK_BYTES
    }
