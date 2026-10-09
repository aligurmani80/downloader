import re
from typing import Dict, Any, List, Optional
import yt_dlp
from config import NODE_PATH, FFMPEG_DIR

def format_bytes(size_bytes: Optional[int]) -> str:
    if not size_bytes or size_bytes <= 0:
        return "Unknown size"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

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
    if 'avc1' in v or 'h264' in v or 'x264' in v:
        return 'H.264'
    if 'hev1' in v or 'hvc1' in v or 'h265' in v or 'hevc' in v:
        return 'HEVC'
    return vcodec.split('.')[0].upper()

def get_resolution_label(height: int, width: Optional[int] = None) -> tuple[str, str, int]:
    """
    Returns (resolution_label, tier_name, tier_order)
    """
    effective_height = height
    if width and width > height and effective_height < 4320:
        # Check if ultrawide or special aspect ratio
        if width >= 7000:
            effective_height = 4320
        elif width >= 3500 and effective_height < 2160:
            effective_height = 2160

    if effective_height >= 4320:
        return ("4320p", "8K Ultra HD", 8000)
    elif effective_height >= 2160:
        return ("2160p", "4K Ultra HD", 4000)
    elif effective_height >= 1440:
        return ("1440p", "2K QHD", 2000)
    elif effective_height >= 1080:
        return ("1080p", "Full HD", 1080)
    elif effective_height >= 720:
        return ("720p", "HD", 720)
    elif effective_height >= 480:
        return ("480p", "SD", 480)
    elif effective_height >= 360:
        return ("360p", "Standard", 360)
    elif effective_height >= 240:
        return ("240p", "Low", 240)
    else:
        return ("144p", "Ultra Low", 144)

def extract_video_info(url: str) -> Dict[str, Any]:
    """
    Extracts actual video formats and metadata using yt-dlp.
    Only returns resolutions that are actually available for the given video.
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    if FFMPEG_DIR:
        ydl_opts['ffmpeg_location'] = FFMPEG_DIR
    if NODE_PATH:
        ydl_opts['js_runtimes'] = {'node': {}}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise ValueError("Could not retrieve video information. Please check the URL.")

    formats = info.get('formats', [])
    
    # 1. Detect best audio size to add to video size estimations
    best_audio_size = 0
    best_audio_bitrate = 0
    audio_formats = []
    for f in formats:
        if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
            abr = f.get('abr') or 0
            size = f.get('filesize') or f.get('filesize_approx') or 0
            if size > best_audio_size:
                best_audio_size = size
            if abr > best_audio_bitrate:
                best_audio_bitrate = abr
            audio_formats.append({
                'format_id': f.get('format_id'),
                'acodec': f.get('acodec'),
                'abr': abr,
                'filesize': size,
                'filesize_str': format_bytes(size),
                'ext': f.get('ext')
            })

    # 2. Group video streams by resolution
    res_groups: Dict[int, Dict[str, Any]] = {}
    all_codecs = set()

    for f in formats:
        vcodec = f.get('vcodec')
        if not vcodec or vcodec == 'none':
            continue
        
        height = f.get('height')
        width = f.get('width')
        if not height:
            continue

        codec_family = identify_codec(vcodec)
        all_codecs.add(codec_family)

        fps = f.get('fps') or 30
        filesize = f.get('filesize') or f.get('filesize_approx') or 0
        tbr = f.get('tbr') or 0
        vbr = f.get('vbr') or 0
        dynamic_range = f.get('dynamic_range') or 'SDR'
        format_id = f.get('format_id')
        ext = f.get('ext') or 'mp4'

        res_tag, tier_name, tier_order = get_resolution_label(height, width)

        if height not in res_groups:
            res_groups[height] = {
                'height': height,
                'width': width or 0,
                'res_tag': res_tag,
                'tier_name': tier_name,
                'tier_order': tier_order,
                'max_fps': fps,
                'dynamic_range': dynamic_range,
                'codecs': {},  # codec_family -> format details
                'max_video_size': filesize,
                'format_ids': []
            }
        
        group = res_groups[height]
        if fps > group['max_fps']:
            group['max_fps'] = fps
        if dynamic_range != 'SDR':
            group['dynamic_range'] = dynamic_range
        if filesize > group['max_video_size']:
            group['max_video_size'] = filesize

        group['format_ids'].append(format_id)

        # Store format details per codec
        if codec_family not in group['codecs']:
            group['codecs'][codec_family] = {
                'codec': codec_family,
                'raw_vcodec': vcodec,
                'format_id': format_id,
                'filesize': filesize,
                'fps': fps,
                'ext': ext,
                'tbr': tbr
            }
        else:
            # Keep higher bitrate format if multiple exist for same codec
            existing = group['codecs'][codec_family]
            if (tbr and tbr > (existing.get('tbr') or 0)) or (filesize > (existing.get('filesize') or 0)):
                group['codecs'][codec_family] = {
                    'codec': codec_family,
                    'raw_vcodec': vcodec,
                    'format_id': format_id,
                    'filesize': filesize,
                    'fps': fps,
                    'ext': ext,
                    'tbr': tbr
                }

    # 3. Build cleanly sorted resolutions list (highest first)
    available_resolutions = []
    has_8k = False
    has_4k = False
    has_hdr = False

    for height in sorted(res_groups.keys(), reverse=True):
        group = res_groups[height]
        if height >= 4320:
            has_8k = True
        elif height >= 2160:
            has_4k = True
        if group['dynamic_range'] != 'SDR':
            has_hdr = True

        total_est_bytes = group['max_video_size'] + best_audio_size if group['max_video_size'] > 0 else 0
        codec_list = sorted(list(group['codecs'].keys()), key=lambda c: 0 if c == 'AV1' else (1 if c == 'VP9' else 2))

        # Build codec explanation note
        codec_note = ""
        if height >= 4320:
            codec_note = "8K master stream in AV1/VP9 (YouTube standard). Unmatched sharpness."
        elif height >= 2160:
            codec_note = "4K UHD in AV1/VP9 for optimal compression and color precision."
        elif "H.264" in codec_list:
            codec_note = "H.264 available for universal device compatibility."
        else:
            codec_note = "AV1 / VP9 modern streaming codecs."

        available_resolutions.append({
            'height': height,
            'width': group['width'],
            'res_tag': group['res_tag'],
            'tier_name': group['tier_name'],
            'full_label': f"{group['res_tag']} - {group['tier_name']}",
            'fps': int(group['max_fps']) if group['max_fps'] else 30,
            'is_hdr': group['dynamic_range'] != 'SDR',
            'dynamic_range': group['dynamic_range'],
            'codecs': codec_list,
            'codec_details': group['codecs'],
            'filesize_bytes': total_est_bytes,
            'filesize_str': format_bytes(total_est_bytes),
            'codec_note': codec_note,
            'format_ids': group['format_ids']
        })

    # Codec compatibility summary notes
    compatibility_notes = []
    if has_8k:
        compatibility_notes.append("8K (4320p) detected! 8K is served exclusively in AV1 or VP9. Standard players can play AV1 via VLC or Windows AV1 Video Extension.")
    if "H.264" in all_codecs:
        max_h264_res = max([r['height'] for r in available_resolutions if 'H.264' in r['codecs']], default=1080)
        compatibility_notes.append(f"H.264 (AVC) is available up to {max_h264_res}p. For 1440p, 4K, and 8K, YouTube uses AV1 & VP9.")
    else:
        compatibility_notes.append("This video uses modern AV1/VP9 stream encoding across all resolutions.")

    duration_sec = info.get('duration') or 0

    return {
        'id': info.get('id'),
        'title': info.get('title'),
        'description': (info.get('description') or '')[:300],
        'thumbnail': info.get('thumbnail'),
        'duration_seconds': duration_sec,
        'duration_formatted': format_duration(duration_sec),
        'channel': info.get('uploader') or info.get('channel') or "Unknown Channel",
        'channel_url': info.get('uploader_url') or info.get('channel_url'),
        'view_count': info.get('view_count'),
        'webpage_url': info.get('webpage_url') or url,
        'has_8k': has_8k,
        'has_4k': has_4k,
        'has_hdr': has_hdr,
        'max_resolution': available_resolutions[0]['full_label'] if available_resolutions else "Unknown",
        'resolutions': available_resolutions,
        'all_codecs': sorted(list(all_codecs)),
        'best_audio_bitrate': best_audio_bitrate,
        'compatibility_notes': compatibility_notes
    }
