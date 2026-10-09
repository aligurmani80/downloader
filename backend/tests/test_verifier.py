import subprocess
from pathlib import Path
import pytest
from app.config import FFMPEG_PATH
from app.verifier import verify_media_file, ensure_compatible_mp4, VerificationError

@pytest.fixture(scope="module")
def media_samples(tmp_path_factory):
    """
    Generates synthetic media samples using FFmpeg to test verifier and transcoder.
    """
    tmp_dir = tmp_path_factory.mktemp("test_media")

    valid_video = tmp_dir / "valid_video.mp4"
    audio_only_fake_mp4 = tmp_dir / "audio_renamed_as_video.mp4"
    valid_audio_mp3 = tmp_dir / "valid_audio.mp3"

    # 1. Generate 1 second valid MP4 with H.264 video and AAC audio
    cmd_valid = [
        FFMPEG_PATH, "-y",
        "-f", "lavfi", "-i", "color=c=blue:s=320x240:d=1:r=25",
        "-f", "lavfi", "-i", "sine=f=440:d=1",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(valid_video)
    ]
    subprocess.run(cmd_valid, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    # 2. Generate 1 second audio-only file but name it .mp4 (simulates the critical bug!)
    cmd_audio_only = [
        FFMPEG_PATH, "-y",
        "-f", "lavfi", "-i", "sine=f=440:d=1",
        "-c:a", "aac", "-b:a", "128k",
        str(audio_only_fake_mp4)
    ]
    subprocess.run(cmd_audio_only, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    # 3. Generate 1 second MP3 file
    cmd_mp3 = [
        FFMPEG_PATH, "-y",
        "-f", "lavfi", "-i", "sine=f=440:d=1",
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(valid_audio_mp3)
    ]
    subprocess.run(cmd_mp3, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    return {
        "valid_video": valid_video,
        "audio_only_fake_mp4": audio_only_fake_mp4,
        "valid_audio_mp3": valid_audio_mp3,
        "tmp_dir": tmp_dir
    }

def test_verify_valid_video(media_samples):
    result = verify_media_file(media_samples["valid_video"], expected_type="video")
    assert result["verified"] is True
    assert result["type"] == "video"
    assert result["width"] == 320
    assert result["height"] == 240
    assert result["video_codec"] == "h264"
    assert result["audio_codec"] == "aac"

def test_reject_audio_only_disguised_as_video(media_samples):
    """
    CRITICAL BUG REGRESSION TEST:
    Verifies that an audio file renamed to .mp4 or without video track is rejected.
    """
    with pytest.raises(VerificationError) as exc_info:
        verify_media_file(media_samples["audio_only_fake_mp4"], expected_type="video")
    
    assert "NO visible video track" in str(exc_info.value)

def test_verify_valid_audio(media_samples):
    result = verify_media_file(media_samples["valid_audio_mp3"], expected_type="audio")
    assert result["verified"] is True
    assert result["type"] == "audio"
    assert result["audio_codec"] == "mp3"

def test_ensure_compatible_mp4(media_samples):
    out_path = media_samples["tmp_dir"] / "transcoded_compat.mp4"
    result_path = ensure_compatible_mp4(media_samples["valid_video"], out_path)
    assert result_path.exists()
    
    verified = verify_media_file(result_path, expected_type="video")
    assert verified["verified"] is True
    assert verified["video_codec"] == "h264"
    assert verified["pix_fmt"] == "yuv420p"
