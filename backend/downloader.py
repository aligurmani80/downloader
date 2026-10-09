import os
import sys
import json
import re
import time
import uuid
import datetime
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

import yt_dlp

DOWNLOADS_DIR = Path(__file__).resolve().parent.parent / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = Path(__file__).resolve().parent / "data" / "downloads_history.json"
HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

# In-memory progress tracking dict
# task_id -> progress dict
active_tasks: Dict[str, Dict[str, Any]] = {}
tasks_lock = threading.Lock()

def detect_platform(url: str) -> Dict[str, str]:
    """Detect platform from URL."""
    try:
        domain = urlparse(url).netloc.lower()
        path = urlparse(url).path.lower()
    except Exception:
        domain = url.lower()
        path = ""

    if "youtube.com" in domain or "youtu.be" in domain:
        return {"name": "YouTube", "icon": "youtube", "color": "#FF0000"}
    elif "tiktok.com" in domain:
        return {"name": "TikTok", "icon": "tiktok", "color": "#FE2C55"}
    elif "instagram.com" in domain or "instagr.am" in domain:
        return {"name": "Instagram", "icon": "instagram", "color": "#E1306C"}
    elif "twitter.com" in domain or "x.com" in domain:
        return {"name": "X (Twitter)", "icon": "twitter", "color": "#1DA1F2"}
    elif "facebook.com" in domain or "fb.watch" in domain:
        return {"name": "Facebook", "icon": "facebook", "color": "#1877F2"}
    elif "reddit.com" in domain:
        return {"name": "Reddit", "icon": "reddit", "color": "#FF4500"}
    elif "vimeo.com" in domain:
        return {"name": "Vimeo", "icon": "vimeo", "color": "#1AB7EA"}
    elif "twitch.tv" in domain:
        return {"name": "Twitch", "icon": "twitch", "color": "#9146FF"}
    else:
        return {"name": "Web Video", "icon": "globe", "color": "#8B5CF6"}

def format_bytes(size: Optional[int]) -> Optional[str]:
    if not size or size <= 0:
        return None
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def format_duration(seconds: Optional[int]) -> Optional[str]:
    if not seconds or seconds < 0:
        return None
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def extract_info_safe(url: str) -> Dict[str, Any]:
    """Safely extract metadata from URL using yt_dlp."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,
        'socket_timeout': 15,
        'no_color': True,
        'ignoreerrors': False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info

def parse_metadata(info: Dict[str, Any], url: str) -> Dict[str, Any]:
    """Parse raw yt_dlp info into clean, structured UI friendly metadata."""
    platform_info = detect_platform(url)
    
    raw_formats = info.get('formats', [])
    video_formats: List[Dict[str, Any]] = []
    audio_formats: List[Dict[str, Any]] = []
    
    # Track available resolution heights that actually exist
    seen_heights = set()
    height_map = {
        144: "144p",
        240: "240p",
        360: "360p",
        480: "480p",
        720: "720p (HD)",
        1080: "1080p (Full HD)",
        1440: "1440p (2K)",
        2160: "2160p (4K UHD)",
        4320: "4320p (8K UHD)",
    }

    # Group formats by height
    # Keep the best quality format per height
    best_by_height: Dict[int, Dict[str, Any]] = {}
    
    for f in raw_formats:
        vcodec = f.get('vcodec', 'none')
        acodec = f.get('acodec', 'none')
        height = f.get('height')
        width = f.get('width')
        filesize = f.get('filesize') or f.get('filesize_approx')
        fps = f.get('fps')
        ext = f.get('ext', 'mp4')
        format_id = f.get('format_id')
        
        # Audio-only stream
        if vcodec == 'none' and acodec != 'none':
            abr = f.get('abr') or f.get('tbr')
            audio_formats.append({
                "format_id": format_id,
                "ext": ext,
                "abr": abr,
                "quality_label": f"{int(abr)} kbps" if abr else "Standard Audio",
                "filesize_approx": filesize,
                "filesize_str": format_bytes(filesize),
                "acodec": acodec,
            })
            continue
            
        # Video stream
        if vcodec != 'none' and height and height > 0:
            seen_heights.add(height)
            # Find closest standard target or record height
            curr_best = best_by_height.get(height)
            # We prefer formats with higher bitrate, or mp4 if available
            tbr = f.get('tbr') or 0
            curr_tbr = (curr_best.get('tbr') or 0) if curr_best else -1
            
            if not curr_best or tbr > curr_tbr or (tbr == curr_tbr and ext == 'mp4'):
                has_audio = (acodec != 'none')
                best_by_height[height] = {
                    "format_id": format_id,
                    "resolution": height_map.get(height, f"{height}p"),
                    "height": height,
                    "width": width,
                    "fps": fps,
                    "ext": ext if ext in ['mp4', 'webm'] else 'mp4',
                    "filesize_approx": filesize,
                    "filesize_str": format_bytes(filesize),
                    "vcodec": vcodec,
                    "acodec": acodec if acodec != 'none' else None,
                    "has_audio": has_audio,
                    "tbr": tbr,
                    "note": f.get('format_note') or ''
                }

    # Sort video formats descending by height
    sorted_heights = sorted(best_by_height.keys(), reverse=True)
    for h in sorted_heights:
        v_item = best_by_height[h]
        v_item.pop('tbr', None)
        video_formats.append(v_item)

    # If no separate video formats found (e.g. direct stream)
    if not video_formats and (info.get('height') or info.get('url')):
        h = info.get('height') or 720
        video_formats.append({
            "format_id": "best",
            "resolution": height_map.get(h, f"{h}p"),
            "height": h,
            "width": info.get('width'),
            "fps": info.get('fps'),
            "ext": info.get('ext', 'mp4'),
            "filesize_approx": info.get('filesize'),
            "filesize_str": format_bytes(info.get('filesize')),
            "vcodec": info.get('vcodec'),
            "acodec": info.get('acodec'),
            "has_audio": True,
            "note": "Standard stream"
        })
        seen_heights.add(h)

    # Deduplicate and sort audio formats by bitrate
    audio_formats.sort(key=lambda x: x.get('abr') or 0, reverse=True)
    # Also add standard exported audio profiles: MP3 320k, MP3 192k, M4A, WAV
    standard_audio_options = [
        {"format_id": "bestaudio_mp3_320", "ext": "mp3", "abr": 320, "quality_label": "MP3 - 320 kbps (High Quality)", "filesize_approx": None, "filesize_str": None, "acodec": "mp3"},
        {"format_id": "bestaudio_mp3_192", "ext": "mp3", "abr": 192, "quality_label": "MP3 - 192 kbps (Standard)", "filesize_approx": None, "filesize_str": None, "acodec": "mp3"},
        {"format_id": "bestaudio_m4a", "ext": "m4a", "abr": 160, "quality_label": "M4A - AAC Audio", "filesize_approx": None, "filesize_str": None, "acodec": "aac"},
        {"format_id": "bestaudio_wav", "ext": "wav", "abr": None, "quality_label": "WAV - Lossless Uncompressed", "filesize_approx": None, "filesize_str": None, "acodec": "pcm_s16le"},
        {"format_id": "bestaudio_opus", "ext": "opus", "abr": 128, "quality_label": "Opus - Ultra-Efficient Audio", "filesize_approx": None, "filesize_str": None, "acodec": "opus"},
    ]

    # Clean thumbnail URL
    thumbnail = info.get('thumbnail')
    if not thumbnail and info.get('thumbnails'):
        # Pick the largest thumbnail
        thumbs = info.get('thumbnails', [])
        thumbs_with_width = [t for t in thumbs if t.get('width')]
        if thumbs_with_width:
            thumbs_with_width.sort(key=lambda t: t.get('width', 0), reverse=True)
            thumbnail = thumbs_with_width[0].get('url')
        elif thumbs:
            thumbnail = thumbs[-1].get('url')

    duration_sec = info.get('duration')
    available_res_labels = [v['resolution'] for v in video_formats]

    return {
        "id": str(info.get('id', uuid.uuid4().hex[:8])),
        "url": url,
        "title": info.get('title', 'Unknown Media Title'),
        "thumbnail": thumbnail,
        "duration": duration_sec,
        "duration_str": format_duration(duration_sec),
        "uploader": info.get('uploader') or info.get('channel') or info.get('creator') or platform_info['name'],
        "uploader_url": info.get('uploader_url'),
        "platform": platform_info['name'],
        "platform_icon": platform_info['icon'],
        "description": (info.get('description') or '')[:300],
        "view_count": info.get('view_count'),
        "video_formats": video_formats,
        "audio_formats": standard_audio_options + audio_formats[:3],
        "available_resolutions": available_res_labels,
    }

def sanitize_filename(name: str) -> str:
    """Remove illegal characters from file names."""
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    return clean[:120].strip()

def load_history() -> List[Dict[str, Any]]:
    """Load download history from JSON file."""
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            items = json.load(f)
            # Verify file availability
            for item in items:
                filepath = DOWNLOADS_DIR / item.get("filename", "")
                item["is_available"] = filepath.exists()
                if item["is_available"]:
                    try:
                        item["filesize"] = filepath.stat().st_size
                        item["filesize_str"] = format_bytes(item["filesize"])
                    except Exception:
                        pass
            return items
    except Exception as e:
        print(f"Error loading history: {e}")
        return []

def save_history_item(item: Dict[str, Any]):
    """Append item to history and save to JSON."""
    history = load_history()
    # Remove existing item with same id if any
    history = [h for h in history if h.get("id") != item.get("id")]
    history.insert(0, item)
    # Keep max 100 history items
    history = history[:100]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving history: {e}")

def delete_history_item(item_id: str) -> bool:
    """Delete item from history."""
    history = load_history()
    new_history = [h for h in history if h.get("id") != item_id]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(new_history, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

def clear_all_history() -> bool:
    """Clear all history items."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return True
    except Exception:
        return False

def start_download_task(
    url: str,
    format_type: str,
    quality: Optional[str] = None,
    format_id: Optional[str] = None,
    container: Optional[str] = "mp4",
    title: Optional[str] = None,
    thumbnail: Optional[str] = None,
) -> str:
    """Start background download task and return task_id."""
    task_id = str(uuid.uuid4())
    
    with tasks_lock:
        active_tasks[task_id] = {
            "task_id": task_id,
            "url": url,
            "status": "queued",
            "percent": 0.0,
            "downloaded_bytes": 0,
            "total_bytes": 0,
            "speed": 0.0,
            "speed_str": None,
            "eta": None,
            "eta_str": None,
            "filename": None,
            "filepath": None,
            "download_url": None,
            "error": None,
            "title": title or "Media",
            "thumbnail": thumbnail,
            "resolution": quality,
            "format_type": format_type,
            "ext": container or ("mp3" if format_type == "audio" else "mp4"),
            "created_at": time.time(),
        }

    thread = threading.Thread(
        target=_download_worker,
        args=(task_id, url, format_type, quality, format_id, container, title, thumbnail),
        daemon=True,
    )
    thread.start()
    return task_id

def _download_worker(
    task_id: str,
    url: str,
    format_type: str,
    quality: Optional[str],
    format_id: Optional[str],
    container: Optional[str],
    title: Optional[str],
    thumbnail: Optional[str],
):
    """Worker function executing yt_dlp download and tracking progress."""
    outtmpl = str(DOWNLOADS_DIR / "%(title).100s [%(id)s].%(ext)s")
    final_filepath: Optional[str] = None
    final_filename: Optional[str] = None
    resolved_title = title

    def progress_hook(d):
        nonlocal final_filepath, final_filename
        status = d.get('status')
        with tasks_lock:
            task = active_tasks.get(task_id)
            if not task:
                return

            if status == 'downloading':
                task['status'] = 'downloading'
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                task['downloaded_bytes'] = downloaded
                task['total_bytes'] = total
                
                if total > 0:
                    task['percent'] = round((downloaded / total) * 100, 1)
                else:
                    # Fallback percent from yt_dlp _percent_str
                    p_str = d.get('_percent_str', '').strip().replace('%', '')
                    try:
                        task['percent'] = round(float(p_str), 1)
                    except Exception:
                        pass
                
                speed = d.get('speed')
                if speed:
                    task['speed'] = speed
                    task['speed_str'] = format_bytes(speed) + "/s" if speed else None
                
                eta = d.get('eta')
                if eta is not None:
                    task['eta'] = eta
                    task['eta_str'] = format_duration(eta)
                
                cur_filename = d.get('filename')
                if cur_filename:
                    final_filepath = cur_filename
                    final_filename = os.path.basename(cur_filename)
                    task['filename'] = final_filename

            elif status == 'finished':
                # Downloading done, now converting / merging
                task['status'] = 'merging'
                task['percent'] = 98.0
                task['speed_str'] = None
                task['eta_str'] = "Finishing..."
                cur_filename = d.get('filename')
                if cur_filename:
                    final_filepath = cur_filename
                    final_filename = os.path.basename(cur_filename)
                    task['filename'] = final_filename

    def postprocessor_hook(d):
        nonlocal final_filepath, final_filename
        status = d.get('status')
        with tasks_lock:
            task = active_tasks.get(task_id)
            if not task:
                return
            if status == 'started':
                task['status'] = 'converting'
                task['eta_str'] = "Processing media..."
            elif status == 'finished':
                task['status'] = 'merging'

    # Configure yt_dlp options
    ydl_opts: Dict[str, Any] = {
        'outtmpl': outtmpl,
        'progress_hooks': [progress_hook],
        'postprocessor_hooks': [postprocessor_hook],
        'quiet': True,
        'no_warnings': True,
        'no_color': True,
        'overwrites': True,
        'windowsfilenames': True,
    }

    # Audio vs Video selection
    if format_type == "audio":
        audio_format = container or "mp3"
        # Determine audio quality bitrate
        preferred_quality = "192"
        if quality and "320" in quality:
            preferred_quality = "320"
        elif quality and "128" in quality:
            preferred_quality = "128"

        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': audio_format if audio_format in ['mp3', 'm4a', 'wav', 'opus', 'aac', 'flac'] else 'mp3',
            'preferredquality': preferred_quality,
        }]
    else:
        # Video download
        target_container = container or "mp4"
        # Parse requested height from quality e.g. "1080p" -> 1080
        match_h = re.search(r'(\d+)p', quality or '')
        if match_h:
            h = match_h.group(1)
            # Combine best video with matching height and best audio
            ydl_opts['format'] = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
        elif format_id and format_id != "best":
            ydl_opts['format'] = f"{format_id}+bestaudio/best"
        else:
            ydl_opts['format'] = "bestvideo+bestaudio/best"

        # Remux or merge into chosen container
        ydl_opts['merge_output_format'] = target_container

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            extract_data = ydl.extract_info(url, download=True)
            if extract_data:
                resolved_title = extract_data.get('title') or resolved_title

        # Determine the real file that was created
        # Check actual files on disk
        found_path = None
        if final_filepath and os.path.exists(final_filepath):
            found_path = final_filepath
        else:
            # Check with extension replacement
            if final_filepath:
                base_without_ext = os.path.splitext(final_filepath)[0]
                expected_ext = container or ("mp3" if format_type == "audio" else "mp4")
                candidate = f"{base_without_ext}.{expected_ext}"
                if os.path.exists(candidate):
                    found_path = candidate

        # If still not found, check most recent file in downloads directory
        if not found_path:
            recent_files = sorted(DOWNLOADS_DIR.glob("*"), key=os.path.getmtime, reverse=True)
            if recent_files and (time.time() - recent_files[0].stat().st_mtime) < 120:
                found_path = str(recent_files[0])

        if found_path and os.path.exists(found_path):
            actual_filename = os.path.basename(found_path)
            actual_size = os.path.getsize(found_path)
            
            with tasks_lock:
                task = active_tasks.get(task_id)
                if task:
                    task['status'] = 'finished'
                    task['percent'] = 100.0
                    task['filename'] = actual_filename
                    task['filepath'] = found_path
                    task['download_url'] = f"/api/downloads/file/{actual_filename}"
                    task['total_bytes'] = actual_size
                    task['downloaded_bytes'] = actual_size
                    task['speed_str'] = None
                    task['eta_str'] = "Complete"
                    task['title'] = resolved_title or task['title']

            # Record in history
            history_item = {
                "id": str(uuid.uuid4()),
                "task_id": task_id,
                "title": resolved_title or "Downloaded Media",
                "thumbnail": thumbnail,
                "platform": detect_platform(url)['name'],
                "format_type": format_type,
                "resolution": quality,
                "ext": os.path.splitext(actual_filename)[1].lstrip('.'),
                "filesize": actual_size,
                "filesize_str": format_bytes(actual_size),
                "download_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "filename": actual_filename,
                "is_available": True,
                "download_url": f"/api/downloads/file/{actual_filename}",
            }
            save_history_item(history_item)
        else:
            raise Exception("File was not saved to expected destination.")

    except Exception as e:
        error_msg = str(e)
        print(f"Download failed for task {task_id}: {error_msg}")
        with tasks_lock:
            task = active_tasks.get(task_id)
            if task:
                task['status'] = 'error'
                task['error'] = error_msg
                task['speed_str'] = None
                task['eta_str'] = None
