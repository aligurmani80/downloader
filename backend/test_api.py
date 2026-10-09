import pytest
from fastapi.testclient import TestClient
from main import app
from format_detector import identify_codec, get_resolution_label, format_bytes, format_duration
from download_manager import download_manager

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "yt_dlp_version" in data
    assert data["ffmpeg_available"] is True
    assert data["ffprobe_available"] is True
    assert "disk" in data
    assert data["disk"]["free_gb"] > 0

def test_codec_identification():
    assert identify_codec("av01.0.08M.08") == "AV1"
    assert identify_codec("vp09.00.41.08") == "VP9"
    assert identify_codec("vp9") == "VP9"
    assert identify_codec("avc1.640028") == "H.264"
    assert identify_codec("hev1.1.6.L93.B0") == "HEVC"
    assert identify_codec("none") == "Unknown"

def test_resolution_tier_classification():
    # 8K
    tag, tier, order = get_resolution_label(4320, 7680)
    assert tag == "4320p"
    assert "8K" in tier
    assert order == 8000

    # 4K
    tag, tier, order = get_resolution_label(2160, 3840)
    assert tag == "2160p"
    assert "4K" in tier

    # 2K / 1440p
    tag, tier, order = get_resolution_label(1440, 2560)
    assert tag == "1440p"
    assert "2K" in tier

    # 1080p
    tag, tier, order = get_resolution_label(1080, 1920)
    assert tag == "1080p"
    assert "Full HD" in tier

    # 720p
    tag, tier, order = get_resolution_label(720, 1280)
    assert tag == "720p"

def test_formatting_utilities():
    assert format_bytes(1024 * 1024 * 500) == "500.0 MB"
    assert format_bytes(1024 * 1024 * 1024 * 2) == "2.0 GB"
    assert format_duration(65) == "01:05"
    assert format_duration(3665) == "01:01:05"

def test_strict_audio_only_rejection():
    # Test that verify_download_file raises an error if no video stream exists
    import tempfile
    import os
    # Create dummy file with fake data
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(b"0" * 200000)
        temp_path = f.name
    
    try:
        with pytest.raises(Exception):
            download_manager._verify_download_file(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_info_validation():
    # Empty url should return 400
    resp = client.post("/api/info", json={"url": "   "})
    assert resp.status_code == 400
