import os
import re
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify, send_file
import yt_dlp

app = Flask(__name__, static_folder="static", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

ALLOWED_HOSTS = {
    "instagram.com", "www.instagram.com", "m.instagram.com",
    "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be",
    "music.youtube.com"
}

def valid_media_url(value):
    from urllib.parse import urlparse
    try:
        parsed = urlparse(value)
        host = (parsed.hostname or "").lower()
        return parsed.scheme in ("http", "https") and any(
            host == allowed or host.endswith("." + allowed)
            for allowed in ALLOWED_HOSTS
        )
    except Exception:
        return False

def safe_filename(name, fallback="media"):
    name = re.sub(r'[^A-Za-z0-9._ -]+', '', name or "").strip(" .")
    return (name[:100] or fallback)

@app.get("/")
def home():
    return app.send_static_file("index.html")

@app.post("/api/download")
def download():
    data = request.get_json(silent=True) or {}
    url = str(data.get("url", "")).strip()
    kind = str(data.get("kind", "")).strip()
    fmt = str(data.get("format", "")).strip().lower()

    if not valid_media_url(url):
        return jsonify(error="Please use a public Instagram or YouTube URL."), 400
    if kind not in {"igVideo", "igAudio", "ytAudio"}:
        return jsonify(error="Unsupported download type."), 400
    if kind.startswith("ig") and not ("instagram.com" in url.lower()):
        return jsonify(error="For this option, paste an Instagram link."), 400
    if kind == "ytAudio" and not any(host in url.lower() for host in ("youtube.com", "youtu.be")):
        return jsonify(error="For YouTube Audio, paste a YouTube link."), 400

    # Temporary directory is removed automatically after the response completes.
    temp_dir = tempfile.TemporaryDirectory(prefix="instayt_")
    outtmpl = str(Path(temp_dir.name) / "%(title).80s-%(id)s.%(ext)s")
    audio_only = kind in {"igAudio", "ytAudio"}

    if audio_only:
        if fmt not in {"mp3", "m4a"}:
            fmt = "mp3"
        postprocessors = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": fmt,
            "preferredquality": "192",
        }]
        format_selector = "bestaudio/best"
    else:
        # 1018p is not a standard target; interpret the requested option as 1080p.
        height = 720 if fmt == "720p" else 1080
        format_selector = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best[height<={height}]"
        postprocessors = []

    options = {
        "outtmpl": outtmpl,
        "format": format_selector,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "max_filesize": 500 * 1024 * 1024,
        "socket_timeout": 20,
        "retries": 1,
        "fragment_retries": 1,
        "postprocessors": postprocessors,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            title = safe_filename(info.get("title", "download"))
        files = [p for p in Path(temp_dir.name).iterdir() if p.is_file()]
        if not files:
            raise RuntimeError("The source did not produce a downloadable file.")
        # Prefer final postprocessed file; yt-dlp may leave intermediate files.
        candidates = [p for p in files if p.suffix.lower() in
                      ({".mp3", ".m4a"} if audio_only else {".mp4", ".mkv", ".webm", ".mov"})]
        selected = max(candidates or files, key=lambda p: p.stat().st_size)
        mime = "audio/mpeg" if selected.suffix.lower() == ".mp3" else (
            "audio/mp4" if selected.suffix.lower() == ".m4a" else "application/octet-stream"
        )
        response = send_file(selected, as_attachment=True, download_name=f"{title}{selected.suffix}", mimetype=mime)
        response.call_on_close(temp_dir.cleanup)
        return response
    except Exception as exc:
        temp_dir.cleanup()
        # Avoid exposing stack traces or local server paths.
        message = str(exc)
        if "ffmpeg" in message.lower():
            message = "Audio conversion needs FFmpeg installed on the server."
        elif "private" in message.lower() or "login" in message.lower() or "cookies" in message.lower():
            message = "This content may be private or require login. Only public links are supported."
        else:
            message = "Could not download this link. It may be unavailable, unsupported, or restricted."
        return jsonify(error=message), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
