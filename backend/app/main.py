"""Jisr backend.

One FastAPI app that:
  - exposes the API under /api
  - serves the frontend folder at /  (one deploy = one link for the judges)

Run from the repo root:
    uvicorn backend.app.main:app --reload
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT / "frontend"
MOCK_PROJECT = FRONTEND_DIR / "mock" / "project.json"
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "100"))

app = FastAPI(title="Jisr API", version="0.1.0")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/projects/{video_id}")
def get_project(video_id: str):
    """Returns a processed project. For now only the demo exists."""
    if video_id != "demo":
        raise HTTPException(404, "Project not found")
    return json.loads(MOCK_PROJECT.read_text(encoding="utf-8"))


@app.post("/api/process")
async def process_video(file: UploadFile = File(...)):
    """TODO (pipeline owner): speech-to-text -> Quran detection -> matching -> translation.

    Must return the same shape as frontend/mock/project.json (see docs/data-contract.md).
    """
    if not (file.content_type or "").startswith("video/"):
        raise HTTPException(400, "Please upload a video file")
    raise HTTPException(501, "Processing pipeline not implemented yet")


# Must be last: serves index.html, app.js, style.css, mock/, assets/
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
