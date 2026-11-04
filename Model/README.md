---
title: Fluent Meet Sign API
emoji: 🤟
colorFrom: purple
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# Sign detection API (FastAPI + PyTorch DETR)

Part of **Fluent Meet** (Neural Storm 2026, FT-04). See the repository root README for the full project.

- `GET /health` → `{ "status": "ok", "model_loaded": true }`
- `POST /detect` (form field `file`: JPEG/PNG) → detections with label, score and box
- Interactive docs at `/docs`

Environment variables (Space → Settings → Variables): `ALLOWED_ORIGINS` (comma-separated sites allowed to
call the API from a browser — **must include your deployed frontend URL**), `SCORE_THRESHOLD`, `MODEL_URL`.
