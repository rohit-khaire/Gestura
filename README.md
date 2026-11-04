# Gestura

Gestura is a real-time communication app with Stream-powered chat and video calls, plus live sign-language detection over the call view. Users enter a display name instead of creating an account, join the public chat experience, and can start or join calls from the frontend.

## Features

- Anonymous guest sessions with server-generated Stream user IDs and tokens
- Real-time public chat using Stream Chat
- Video calls using the Stream Video React SDK
- Frame-based sign-language detection while a call is active
- Detection overlays showing the label, confidence score, and bounding box
- Responsive React interface with lazy-loaded chat and call pages

## Architecture

The repository contains three independently started services:

| Service | Directory | Development address | Responsibility |
| --- | --- | --- | --- |
| Frontend | `Frontend/` | `http://localhost:5173` | React/Vite UI, Stream clients, frame capture |
| Node backend | `backend/` | `http://localhost:5000` | Guest creation and Stream token generation |
| Detection API | `Model/` | `http://localhost:7860` | FastAPI, PyTorch/DETR inference |

In the current frontend implementation, captured frames are posted directly to the deployed detection API at `https://nick-localhost-sign-detect.hf.space/detect`. To use a local detection service, update the URL in `Frontend/src/pages/CallPage.jsx` to `http://localhost:7860/detect`.

## Tech Stack

- **Frontend:** React 19, Vite, React Router 7, Tailwind CSS 4, TanStack React Query, Stream Chat, Stream Video, Axios
- **Backend:** Node.js, Express 5, Stream Chat SDK
- **Model service:** Python 3.12, FastAPI, Uvicorn, PyTorch, DETR, OpenCV

## Setup

### 1. Start the Node backend

Create `backend/.env`:

```env
PORT=5000
NODE_ENV=development
STREAM_API_KEY=your_stream_api_key
STREAM_API_SECRET=your_stream_api_secret
```

Then run:

```bash
cd backend
npm install
npm run dev
```

The backend exposes `POST /api/chat/guest` and expects `{ "name": "..." }`. It returns `{ id, name, token }` for the Stream client.

### 2. Start the frontend

Create `Frontend/.env`:

```env
VITE_STREAM_API_KEY=your_stream_api_key
```

Then run:

```bash
cd Frontend
npm install
npm run dev
```

Open `http://localhost:5173` in a browser. The frontend uses `http://localhost:5000/api` for the backend in development.

### 3. Run the detection API locally (optional)

The hosted detection API is used by default. To run the model locally, install the Python dependencies and start FastAPI:

```bash
cd Model
pip install -r requirements.txt
uvicorn src.api:app --host 0.0.0.0 --port 7860
```

The model downloads `pretrained/4426_model.pt` from Hugging Face on first startup if the checkpoint is not already present. The API accepts a multipart image upload at `POST /detect` using the `file` field:

```json
{
	"detections": [
		{
			"label": "...",
			"score": 0.95,
			"bbox": [12.0, 24.0, 180.0, 220.0]
		}
	]
}
```

## Detection flow

1. The call page samples the active video element every 500 ms.
2. Each frame is resized to a maximum width of 640 pixels and uploaded as `frame.jpg`.
3. The FastAPI service runs DETR inference and filters detections below a 0.90 confidence threshold.
4. The frontend renders returned detections and clears them shortly after they disappear.

## Production

The frontend currently uses these production endpoints:

- Node API: `https://sign-detection-m4sm.onrender.com/api`
- Detection API: `https://nick-localhost-sign-detect.hf.space/detect`

The backend production CORS allowlist is `https://sign-detection.vercel.app`.