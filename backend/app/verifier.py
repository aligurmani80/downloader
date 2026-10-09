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
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
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
    Verifies that the downloaded file contains the required streams.
    - If expected_type == 'video': MUST contain at least one true video stream AND one audio stream.
      Never accepts audio-only files or simple renames.
    - If expected_type == 'audio': MUST contain at least one audio stream.
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
                "CRITICAL VERIFICATION FAILED: Downloaded file has NO visible video track! "
                "The file is audio-only or corrupt. Cannot report as successful video."
            )
        if not audio_streams:
            raise VerificationError(
                "CRITICAL VERIFICATION FAILED: Downloaded file contains video but has NO audio track."
            )
            
        primary_video = video_streams[0]
        primary_audio = audio_streams[0]
        
        return {
            "verified": True,
            "type": "video",
            "video_codec": primary_video.get("codec_name"),
            "pix_fmt": primary_video.get("pix_fmt"),
            "width": int(primary_video.get("width") or 0),
            "height": int(primary_video.get("height") or 0),
            "audio_codec": primary_audio.get("codec_name"),
            "audio_channels": primary_audio.get("channels"),
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
            "audio_codec": primary_audio.get("codec_name"),
            "audio_channels": primary_audio.get("channels"),
            "duration": float(format_info.get("duration") or primary_audio.get("duration") or 0.0),
            "size_bytes": file_path.stat().st_size
        }
    else:
        raise VerificationError(f"Unknown expected type: {expected_type}")

def ensure_compatible_mp4(input_path: Path, output_path: Path) -> Path:
    """
    Checks if the MP4 is encoded with H.264 (yuv420p) and AAC.
    If not, or if codecs are incompatible, transcodes using FFmpeg.
    If already H.264 + AAC, fast-remuxes with -movflags +faststart for instant streaming.
    """
    probe = probe_media_file(input_path)
    streams = probe.get("streams", [])
    
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    
    if not v_stream:
        raise VerificationError("No video stream found in input file.")
        
    v_codec = (v_stream.get("codec_name") or "").lower()
    pix_fmt = (v_stream.get("pix_fmt") or "").lower()
    a_codec = (a_stream.get("codec_name") or "").lower() if a_stream else ""
    
    needs_video_transcode = (v_codec != "h264" or pix_fmt != "yuv420p")
    needs_audio_transcode = (a_codec != "aac") if a_stream else False
    
    cmd = [FFMPEG_PATH, "-y", "-i", str(input_path.resolve())]
    
    if needs_video_transcode:
        cmd.extend(["-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p"])
    else:
        cmd.extend(["-c:v", "copy"])
        
    if a_stream:
        if needs_audio_transcode:
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        else:
            cmd.extend(["-c:a", "copy"])
            
    cmd.extend(["-movflags", "+faststart", str(output_path.resolve())])
    
    logger.info(f"Running ffmpeg conversion: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        logger.error(f"FFmpeg conversion failed: {result.stderr}")
        raise VerificationError(f"FFmpeg transcode failed: {result.stderr.strip()[:300]}")
        
    return output_path
