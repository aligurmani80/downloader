import os
import sys
import yt_dlp

def download(url: str, mode: str = "video"):
    """
    Download video or audio using yt-dlp.
    :param url: Video URL (YouTube, TikTok, Facebook, etc.)
    :param mode: 'video' (MP4 format) or 'audio' (MP3 192kbps)
    """
    # Ensure downloads folder exists
    os.makedirs("downloads", exist_ok=True)

    options = {
        "outtmpl": "downloads/%(title).150B.%(ext)s",
        "noplaylist": True,
    }

    if mode == "audio":
        options.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        })
    else:
        options.update({
            "format": "bv*+ba/b",
            "merge_output_format": "mp4",
        })

    print(f"[*] Starting download ({mode} mode): {url}")
    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])
    print(f"[✓] Download completed! Saved in 'downloads/' folder.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
        target_mode = sys.argv[2] if len(sys.argv) > 2 else "video"
    else:
        print("=== NexaLoad / yt-dlp Downloader ===")
        target_url = input("Enter video URL: ").strip()
        target_mode = input("Select mode ('video' / 'audio') [Default: video]: ").strip().lower() or "video"

    if target_url and target_url != "PASTE_VIDEO_URL":
        download(target_url, target_mode)
    else:
        print("[!] Please provide a valid URL to download.")
