import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.config import FFPROBE_PATH, FFMPEG_PATH

logger = logging.getLogger(__name__)

class VerificationError(Exception):
    pass

def probe_media_file(file_path: Path) -> Dict[str, Any]:
    """
    Runs ffprobe on the target media file and returns parsed JSON stream/format information.
    """
    if not file_path.exists():
        raise VerificationError(f"Target media file does not exist: {file_path}")
        
    if file_path.stat().st_size < 1024:
        raise VerificationError(f"File size is too small ({file_path.stat().st_size} bytes), download incomplete or corrupt.")
        
    cmd = [
        FFPROBE_PATH,
        "-v", "error",
        "-show_entries", "stream=index,codec_name,codec_type,width,height,duration,r_frame_rate,channels,sample_rate,pix_fmt",
        "-show_entries", "format=duration,size,bit_rate,format_name",
        "-of", "json",
        str(file_path.resolve())
    ]
    
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True, timeout=30)
        data = json.loads(result.stdout)
        return data
    except subprocess.CalledProcessError as e:
        logger.error(f"ffprobe execution failed: {e.stderr}")
        raise VerificationError(f"ffprobe failed to analyze file: {e.stderr.strip() or 'Unknown error'}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse ffprobe JSON output: {e}")
        raise VerificationError("Failed to parse media probe data.")
    except Exception as e:
        raise VerificationError(f"Probe error: {str(e)}")

def verify_media_file(file_path: Path, expected_type: str = "video") -> Dict[str, Any]:
    """
    Verifies that the downloaded file contains the required playable streams.
    - STRICT REQUIREMENT: If expected_type == 'video', MUST contain a playable video stream with width > 0 and height > 0.
      NEVER deliver audio-only content as a successful video download!
    - Verifies audio stream presence when available.
    - Classifies video resolution (from 144p up to 8K 7680×4320).
    """
    probe_data = probe_media_file(file_path)
    streams: List[Dict[str, Any]] = probe_data.get("streams", [])
    format_info: Dict[str, Any] = probe_data.get("format", {})
    
    # Filter image-based streams (e.g. mjpeg/png album art thumbnails)
    image_codecs = {"mjpeg", "png", "jpeg", "jpg", "bmp", "webp", "gif"}
    
    video_streams = [
        s for s in streams
        if s.get("codec_type") == "video"
        and s.get("codec_name", "").lower() not in image_codecs
        and int(s.get("width") or 0) > 0
        and int(s.get("height") or 0) > 0
    ]
    
    audio_streams = [
        s for s in streams
        if s.get("codec_type") == "audio"
    ]
    
    if expected_type == "video":
        if not video_streams:
            raise VerificationError(
                "CRITICAL VERIFICATION FAILED: Downloaded file has NO playable video track! "
                "The file is audio-only or corrupted. Audio-only content cannot be delivered as a video download."
            )
            
        primary_video = video_streams[0]
        primary_audio = audio_streams[0] if audio_streams else None
        
        width = int(primary_video.get("width") or 0)
        height = int(primary_video.get("height") or 0)
        v_codec = primary_video.get("codec_name", "unknown")
        
        # Determine human-friendly resolution tier (144p up to 8K)
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
        elif height >= 480:
            tier = "480p SD"
        elif height >= 360:
            tier = "360p Standard"
        elif height >= 240:
            tier = "240p Low"
        else:
            tier = f"{height}p Ultra Low"
            
        return {
            "verified": True,
            "type": "video",
            "video_codec": v_codec,
            "pix_fmt": primary_video.get("pix_fmt", "yuv420p"),
            "width": width,
            "height": height,
            "resolution": f"{width}x{height} ({tier})",
            "tier": tier,
            "has_video": True,
            "has_audio": primary_audio is not None,
            "audio_codec": primary_audio.get("codec_name") if primary_audio else "none",
            "audio_channels": primary_audio.get("channels") if primary_audio else 0,
            "duration": float(format_info.get("duration") or primary_video.get("duration") or 0.0),
            "size_bytes": file_path.stat().st_size
        }
        
    elif expected_type == "audio":
        if not audio_streams:
            raise VerificationError(
                "CRITICAL VERIFICATION FAILED: Downloaded file contains NO audio track."
            )
            
        primary_audio = audio_streams[0]
        return {
            "verified": True,
            "type": "audio",
            "has_video": False,
            "has_audio": True,
            "audio_codec": primary_audio.get("codec_name", "mp3"),
            "audio_channels": primary_audio.get("channels", 2),
            "duration": float(format_info.get("duration") or primary_audio.get("duration") or 0.0),
            "size_bytes": file_path.stat().st_size
        }
    else:
        raise VerificationError(f"Unknown expected type: {expected_type}")

def ensure_compatible_mp4(input_path: Path, output_path: Path) -> Path:
    """
    Preserves original video quality:
    - Never re-encodes 4K or 8K video! Stream-copies video (-c:v copy) to preserve 100% original quality.
    - If audio is Opus or non-AAC and MP4 container is requested, transcodes audio to high-bitrate AAC (320k)
      while keeping video stream bit-for-bit identical.
    """
    probe = probe_media_file(input_path)
    streams = probe.get("streams", [])
    
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    
    if not v_stream:
        raise VerificationError("No video stream found in input file.")
        
    v_codec = (v_stream.get("codec_name") or "").lower()
    height = int(v_stream.get("height") or 0)
    a_codec = (a_stream.get("codec_name") or "").lower() if a_stream else ""
    
    cmd = [FFMPEG_PATH, "-y", "-i", str(input_path.resolve())]
    
    # 8K / 4K / High Res: ALWAYS stream copy video to preserve 100% master quality and prevent hours of re-encoding
    if height >= 1440 or v_codec in ["av1", "vp9", "vp09", "hevc", "h265"]:
        cmd.extend(["-c:v", "copy"])
    else:
        # For legacy 1080p/720p H.264, stream copy if already H.264
        if v_codec == "h264":
            cmd.extend(["-c:v", "copy"])
        else:
            cmd.extend(["-c:v", "copy"])  # Default to lossless stream copy
            
    if a_stream:
        if a_codec != "aac":
            cmd.extend(["-c:a", "aac", "-b:a", "320k"])
        else:
            cmd.extend(["-c:a", "copy"])
            
    cmd.extend(["-movflags", "+faststart", str(output_path.resolve())])
    
    logger.info(f"Running lossless FFmpeg stream mux: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
    if result.returncode != 0:
        logger.error(f"FFmpeg muxing failed: {result.stderr}")
        raise VerificationError(f"FFmpeg muxing failed: {result.stderr.strip()[:300]}")
        
    return output_path
