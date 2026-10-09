import os
import shutil
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Detect ffmpeg and ffprobe paths
def find_binary(binary_name: str) -> str:
    # 1. System PATH
    found = shutil.which(binary_name)
    if found:
        return found
    
    # 2. Common Windows Winget / Gyan paths
    winget_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
    if os.path.exists(winget_dir):
        for root, dirs, files in os.walk(winget_dir):
            if f"{binary_name}.exe" in files:
                return os.path.join(root, f"{binary_name}.exe")
    
    # 3. Fallback to binary name
    return binary_name

FFMPEG_PATH = find_binary("ffmpeg")
FFPROBE_PATH = find_binary("ffprobe")
FFMPEG_DIR = os.path.dirname(FFMPEG_PATH) if os.path.isabs(FFMPEG_PATH) else None

# Check Node.js runtime for yt-dlp signature extraction
NODE_PATH = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"

# Disk space check: Minimum free disk space required to start download (in bytes)
# 4K/8K videos require at least 5GB free disk space
MIN_FREE_DISK_BYTES = 5 * 1024 * 1024 * 1024  # 5 GB

def get_disk_free_space(path: str = DOWNLOADS_DIR) -> dict:
    total, used, free = shutil.disk_usage(path)
    return {
        "total_bytes": total,
        "used_bytes": used,
        "free_bytes": free,
        "total_gb": round(total / (1024**3), 2),
        "free_gb": round(free / (1024**3), 2),
        "sufficient_for_8k": free > MIN_FREE_DISK_BYTES
    }
