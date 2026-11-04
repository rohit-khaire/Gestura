"""FastAPI service: POST an image frame to /detect, get sign detections back.

Run from the ``Model`` directory:

    python -m uvicorn api:app --app-dir src --port 7860

Settings come from environment variables (see ``Model/.env.example``).
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

import cv2
import numpy as np
import requests
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from inference import Detector

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("api")

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = Path(os.getenv("MODEL_PATH", ROOT / "pretrained" / "4426_model.pt"))
MODEL_URL = os.getenv("MODEL_URL", "https://huggingface.co/Mandarwork/sign/resolve/main/4426_model.pt")
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", "0.90"))  # confidence needed to keep a detection
MAX_DETECTIONS = int(os.getenv("MAX_DETECTIONS", "5"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "https://sign-detection.vercel.app,http://localhost:5173").split(",")
    if o.strip()
]


def download_checkpoint(url: str, dest: Path) -> None:
    """Download to a temp file first so a failed/partial download never looks like a valid model."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    logger.info("Downloading model from %s", url)
    try:
        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            with tmp.open("wb") as f:
                for chunk in response.iter_content(chunk_size=1 << 20):
                    f.write(chunk)
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)
    logger.info("Model saved to %s", dest)


def load_default_detector() -> Detector:
    if not MODEL_PATH.exists():
        download_checkpoint(MODEL_URL, MODEL_PATH)
    return Detector(MODEL_PATH, threshold=SCORE_THRESHOLD, max_detections=MAX_DETECTIONS)


def create_app(load_detector=load_default_detector) -> FastAPI:
    """App factory; tests pass a fake ``load_detector`` so no weights are needed."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.detector = load_detector()
        yield

    app = FastAPI(title="Sign detection API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health(request: Request):
        return {"status": "ok", "model_loaded": getattr(request.app.state, "detector", None) is not None}

    # Plain `def` (not `async def`): FastAPI runs it in a worker thread, so the CPU-heavy model
    # call doesn't block the event loop and other requests (like /health) stay responsive.
    @app.post("/detect")
    def detect(request: Request, file: UploadFile = File(...)):
        data = file.file.read(MAX_UPLOAD_BYTES + 1)
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Image too large")

        frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise HTTPException(status_code=400, detail="Could not decode image")

        start = time.perf_counter()
        detections = request.app.state.detector(frame)
        return {
            "detections": detections,
            "inference_ms": round((time.perf_counter() - start) * 1000, 1),
        }

    return app


app = create_app()
