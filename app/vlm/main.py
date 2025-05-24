import os

from fastapi import FastAPI, HTTPException
from model import describe_video
from pydantic import BaseModel

app = FastAPI()

class VideoRequest(BaseModel):
    video_path: str
    prompt: str = "Describe this video in detail."

@app.post("/describe")
def describe(req: VideoRequest):
    if not os.path.isfile(req.video_path):
        raise HTTPException(status_code=400, detail="Video path does not exist.")

    try:
        result = describe_video(req.video_path, req.prompt)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
