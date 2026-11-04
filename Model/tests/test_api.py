import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

import api


class FakeDetector:
    def __call__(self, frame):
        h, w = frame.shape[:2]
        return [{"class_id": 0, "label": "hello", "score": 0.97, "bbox": [0.0, 0.0, w - 1.0, h - 1.0]}]


def jpeg_bytes(width=64, height=48):
    ok, buf = cv2.imencode(".jpg", np.zeros((height, width, 3), np.uint8))
    assert ok
    return buf.tobytes()


@pytest.fixture
def client():
    with TestClient(api.create_app(load_detector=FakeDetector)) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "model_loaded": True}


def test_detect_returns_detections(client):
    r = client.post("/detect", files={"file": ("frame.jpg", jpeg_bytes(), "image/jpeg")})
    assert r.status_code == 200
    body = r.json()
    assert body["detections"][0]["label"] == "hello"
    assert body["detections"][0]["bbox"] == [0.0, 0.0, 63.0, 47.0]
    assert "inference_ms" in body


def test_detect_rejects_non_images(client):
    r = client.post("/detect", files={"file": ("frame.jpg", b"not an image", "image/jpeg")})
    assert r.status_code == 400


def test_detect_rejects_oversized_uploads(client, monkeypatch):
    monkeypatch.setattr(api, "MAX_UPLOAD_BYTES", 10)
    r = client.post("/detect", files={"file": ("frame.jpg", jpeg_bytes(), "image/jpeg")})
    assert r.status_code == 413
