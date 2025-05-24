from downloader import download_audio, download_subtitles, download_video
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/download/video")
def api_download_video(url: str, quality: int = Query(480)):
    try:
        path = download_video(url, quality)
        return {"status": "success", "path": path}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/download/audio")
def api_download_audio(url: str):
    try:
        path = download_audio(url)
        return {"status": "success", "path": path}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/download/subtitles")
def api_download_subtitles(url: str, lang: str = "en"):
    try:
        content = download_subtitles(url, lang)
        return {"status": "success", "subtitles": content}
    except Exception as e:
        return {"status": "error", "message": str(e)}
