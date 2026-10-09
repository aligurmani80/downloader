import pytest
from app.downloader import fetch_media_info, run_download_job, get_job, jobs, jobs_lock
from app.verifier import verify_media_file
from pathlib import Path

def test_fetch_media_info_youtube():
    # Test with historic short video "Me at the zoo" (19 seconds)
    url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    info = fetch_media_info(url)
    assert info is not None
    assert "zoo" in info["title"].lower()
    assert info["platform"] == "youtube"
    assert len(info["qualities"]) > 0
    assert info["duration_seconds"] > 0

def test_download_and_verify_real_video(tmp_path):
    # Tests real video download, ffmpeg merge, and ffprobe verification
    url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    job_id = "test_e2e_video_job"
    
    with jobs_lock:
        jobs[job_id] = {
            "job_id": job_id,
            "url": url,
            "format_type": "video",
            "quality": "best",
            "status": "pending",
            "progress": 0.0,
            "message": "Starting..."
        }

    run_download_job(job_id, url, format_type="video", quality="best")
    
    job = get_job(job_id)
    assert job["status"] in ("completed", "finished"), f"Job failed: {job.get('error')}"
    assert job["file_path"] is not None
    
    file_path = Path(job["file_path"])
    assert file_path.exists()
    assert file_path.stat().st_size > 10000

    # Verify that the final video contains BOTH an actual video stream and an audio stream!
    verification = verify_media_file(file_path, expected_type="video")
    assert verification["verified"] is True
    assert verification["type"] == "video"
    assert verification["width"] > 0
    assert verification["height"] > 0
    assert verification["video_codec"] == "h264"
    assert verification["audio_codec"] == "aac"

def test_download_and_verify_real_audio(tmp_path):
    # Tests real MP3 audio download and verification
    url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    job_id = "test_e2e_audio_job"
    
    with jobs_lock:
        jobs[job_id] = {
            "job_id": job_id,
            "url": url,
            "format_type": "audio",
            "quality": "mp3",
            "status": "pending",
            "progress": 0.0,
            "message": "Starting..."
        }

    run_download_job(job_id, url, format_type="audio", quality="mp3")
    
    job = get_job(job_id)
    assert job["status"] in ("completed", "finished"), f"Job failed: {job.get('error')}"
    assert job["file_path"] is not None
    
    file_path = Path(job["file_path"])
    assert file_path.exists()
    assert file_path.stat().st_size > 5000
    assert file_path.name.endswith(".mp3")

    verification = verify_media_file(file_path, expected_type="audio")
    assert verification["verified"] is True
    assert verification["type"] == "audio"
    assert verification["audio_codec"] == "mp3"
