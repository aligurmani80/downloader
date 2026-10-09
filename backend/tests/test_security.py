import pytest
from app.security import validate_url, sanitize_filename, detect_platform, is_ip_disallowed

def test_sanitize_filename():
    assert sanitize_filename("Normal Video Title") == "Normal Video Title"
    assert sanitize_filename("../../etc/passwd") == "etcpasswd"
    assert sanitize_filename("video:with*illegal?chars|and<brackets>") == "videowithillegalcharsandbrackets"
    assert sanitize_filename("   leading and trailing spaces.   ") == "leading and trailing spaces"
    assert sanitize_filename("") == "downloaded_media"

def test_detect_platform():
    assert detect_platform("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "youtube"
    assert detect_platform("https://youtu.be/dQw4w9WgXcQ") == "youtube"
    assert detect_platform("https://www.tiktok.com/@user/video/123456789") == "tiktok"
    assert detect_platform("https://vm.tiktok.com/ZM8ABCDEF/") == "tiktok"
    assert detect_platform("https://www.instagram.com/reel/C3zY4vKxN8A/") == "instagram"
    assert detect_platform("https://example.com/video.mp4") == "generic"

def test_is_ip_disallowed():
    # Loopback
    assert is_ip_disallowed("127.0.0.1") is True
    assert is_ip_disallowed("::1") is True
    # Private RFC1918
    assert is_ip_disallowed("10.0.0.1") is True
    assert is_ip_disallowed("192.168.1.1") is True
    assert is_ip_disallowed("172.16.0.1") is True
    # Cloud metadata
    assert is_ip_disallowed("169.254.169.254") is True
    # Public IP
    assert is_ip_disallowed("8.8.8.8") is False
    assert is_ip_disallowed("1.1.1.1") is False

def test_validate_url_ssrf_and_protocols():
    # Disallowed protocols
    valid, err, _ = validate_url("file:///etc/passwd")
    assert valid is False
    assert "Only HTTP and HTTPS" in err

    valid, err, _ = validate_url("ftp://server/video.mp4")
    assert valid is False

    # Localhost and loopback
    valid, err, _ = validate_url("http://localhost:8000/api")
    assert valid is False
    assert "blocked" in err.lower() or "prohibited" in err.lower()

    valid, err, _ = validate_url("http://127.0.0.1:8080/test")
    assert valid is False

    # Embedded credentials
    valid, err, _ = validate_url("http://admin:secret@malicious.com")
    assert valid is False
    assert "credentials" in err.lower()

    # Public valid URLs
    valid, err, plat = validate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert valid is True
    assert err is None
    assert plat == "youtube"
