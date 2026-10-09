from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["ffmpeg_available"] is True
    assert data["ffprobe_available"] is True

def test_info_ssrf_blocking():
    # Attempting to fetch internal resource
    response = client.post("/api/info", json={"url": "http://127.0.0.1:8000/api/health"})
    assert response.status_code == 400
    assert "blocked" in response.json()["detail"].lower() or "prohibited" in response.json()["detail"].lower()

def test_info_invalid_protocol():
    response = client.post("/api/info", json={"url": "file:///c:/windows/system32"})
    assert response.status_code == 400
    assert "HTTP and HTTPS" in response.json()["detail"]

def test_download_invalid_format_type():
    response = client.post("/api/download", json={
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "format_type": "invalid_format",
        "quality": "best"
    })
    assert response.status_code == 400
    assert "Invalid format_type" in response.json()["detail"]
