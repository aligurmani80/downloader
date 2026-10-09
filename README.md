# NexaLoad Pro — Universal Video & Audio Downloader

A modern, high-performance web application designed for downloading publicly available video and audio from **YouTube**, **TikTok**, and **Instagram** for content users own or have authorization to download.

Built with **React**, **Tailwind CSS**, **Python FastAPI**, **yt-dlp**, and **FFmpeg**.

---

## 🌟 Key Features

1. **Intelligent URL Analysis**:
   - Paste video link from YouTube (standard & Shorts), TikTok, or Instagram (Reels & Posts).
   - Real-time platform badge detection.
   - Instant video metadata extraction: title, high-res thumbnail, duration, uploader/channel.

2. **Resolution & Format Flexibility**:
   - High-definition MP4 Video with Audio (1080p Full HD, 720p HD, 480p SD, 360p, or Best Available).
   - Studio-quality MP3 Audio extraction (320 kbps High Fidelity).

3. **Critical Video Bug Fix (Audio-only bug resolved)**:
   - **Root Cause of previous issue**: Previous scripts selected audio-only streams (`bestaudio`) or downloaded separate video/audio DASH streams without proper merging, or left files encoded in VP9/AV1/Opus which fail to display video in common players.
   - **yt-dlp Stream Selection**: Explicitly queries and joins video streams with audio streams (`bestvideo[height<=...]+bestaudio/...`).
   - **FFmpeg Merging & Transcoding**: Post-processes streams into universal H.264 (AVC) video (`-pix_fmt yuv420p`) and AAC stereo audio in standard MP4 containers with `-movflags +faststart`.
   - **ffprobe Deep Verification**: Runs an automated stream probe before completing the download to ensure that an actual video track (`codec_type: video`, positive dimensions) and an audio track are present. Files lacking video tracks are never marked as completed.
   - **In-Browser Playback Testing**: Provides an embedded HTML5 video/audio player to preview and verify real playback inside the browser.

4. **Live Progress Tracking**:
   - Real-time progress bar (percentage, MB/s speed, ETA).
   - Multi-stage pipeline indicator: Stream Resolution → Downloading Streams → FFmpeg Merging/Transcoding → ffprobe Verification → Ready.

5. **Security & System Protection**:
   - **SSRF Defense**: Strict URL parsing and DNS validation blocks requests targeting loopback (`127.0.0.1`, `localhost`), RFC1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local IPs (`169.254.0.0/16`), and cloud metadata IP (`169.254.169.254`).
   - **File Size Caps**: 500 MB limit prevents server disk exhaustion.
   - **Automated Lifecycle Cleanup**: Background cleanup removes temporary download folders older than 30 minutes.
   - **Safe File Naming**: Strips dangerous filesystem and directory traversal characters (`../`, `\`, quotes, colons).
   - **Respects Platform Protections**: Does not attempt to bypass DRM, login walls, or private video protections.

---

## 🏗️ Architecture

```
youtube/
├── backend/
│   ├── app/
│   │   ├── config.py         # Config, limits, paths (FFmpeg/ffprobe)
│   │   ├── downloader.py     # yt-dlp orchestration & progress tracking
│   │   ├── main.py           # FastAPI entrypoint, CORS, background cleanup
│   │   ├── security.py       # SSRF filtering & filename sanitization
│   │   ├── verifier.py       # ffprobe deep stream inspection & transcoding
│   │   └── routes/
│   │       └── api.py        # /health, /info, /analyze, /download, /progress, /file, /preview, /history
│   ├── tests/
│   │   ├── test_api.py       # API integration & error tests
│   │   ├── test_e2e_download.py # Live download & ffprobe stream verification test
│   │   ├── test_security.py  # SSRF protection, platform detection & filename tests
│   │   └── test_verifier.py  # Audio-only regression test, transcoding & ffprobe tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # UrlInputCard, VideoDetailsCard, DownloadProgressCard, CompletedCard, etc.
│   │   ├── context/          # AppContext state management & history
│   │   ├── services/         # API client
│   │   └── App.jsx
│   ├── dist/                 # Production optimized build
│   └── package.json
└── run_server.bat            # One-click startup script
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ (with FFmpeg and ffprobe in PATH)
- Node.js 18+

### 2. Start Application
Simply double-click `run_server.bat` or run:
```powershell
cd backend
venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser at:
`http://localhost:8000`

---

## 🧪 Testing Summary

Automated tests verified via `pytest`:
- `test_health_endpoint`: Checks FFmpeg and ffprobe availability.
- `test_info_ssrf_blocking`: Verifies internal IP / loopback requests are blocked.
- `test_info_invalid_protocol`: Rejects non-HTTP(S) protocols (`file://`, `ftp://`).
- `test_download_invalid_format_type`: Validates format inputs.
- `test_sanitize_filename`: Prevents directory traversal and illegal characters.
- `test_detect_platform`: Correctly classifies YouTube, TikTok, and Instagram URLs.
- `test_is_ip_disallowed`: Validates RFC1918, link-local, and metadata IP filtering.
- `test_reject_audio_only_disguised_as_video`: **Regression test** proving that audio files renamed to `.mp4` are rejected.
- `test_verify_valid_video`: Verifies true video + audio stream detection.
- `test_ensure_compatible_mp4`: Ensures H.264 (yuv420p) and AAC transcoding with faststart.
- `test_fetch_media_info_youtube`: Live metadata extraction test.
- `test_download_and_verify_real_video`: End-to-end video stream merge & ffprobe validation.
- `test_download_and_verify_real_audio`: End-to-end MP3 audio download & validation.
