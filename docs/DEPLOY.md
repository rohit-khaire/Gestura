# Deploy in ~30 minutes

Order matters: model API first (the frontend needs its URL), then the frontend, then (optional) the call backend.

## 1. Model API → Hugging Face Space (free CPU, no ZeroGPU)
1. huggingface.co → **New Space** → SDK **Gradio** → public.
2. In hardware, select **CPU Basic**, not ZeroGPU. Gradio itself does not require ZeroGPU.
3. Upload the **contents of the `Model/` folder** to the Space (drag-and-drop in the web UI, or `git push`).
   `Model/README.md` and `Model/app.py` already carry the Space settings. Don't upload `data/` or `checkpoints/`.
4. The Space installs the Python dependencies and downloads the weights on first start.
5. Space → **Settings → Variables**: `ALLOWED_ORIGINS` = `http://localhost:5173`
   (add the Render URL after the frontend is deployed; the Space restarts).
6. Check: open `https://<user>-<space>.hf.space/health` → `{"status":"ok","model_loaded":true}`.

> The app's built-in default model URL points at someone else's Space whose CORS list won't include *your* site.
> Always set `VITE_DETECT_URL` to your own Space.

## 2. Fallback model API → Render Web Service (free CPU)
If Hugging Face reports a ZeroGPU limit or CPU Basic is unavailable, deploy the model as a Render Web Service.
1. render.com → **New → Web Service** → import the repository → **Root Directory: `Model`**.
2. Build command: `pip install -r requirements.txt`.
3. Start command: `uvicorn api:app --app-dir src --host 0.0.0.0 --port $PORT`.
4. Add `ALLOWED_ORIGINS=https://YOUR-FRONTEND.onrender.com`.
5. Verify `https://YOUR-MODEL.onrender.com/health`.

## 3. Frontend → Render Static Site (free)
1. render.com → **New → Static Site** → import your GitHub repo → **Root Directory: `Frontend`**.
   The repository also includes `render.yaml` for a Blueprint deployment.
2. Build command: `npm install && npm run build`; publish directory: `dist`.
3. Environment variables (set **before** the first build — Vite bakes them in):
   - `VITE_DETECT_URL` = `https://<user>-<space>.hf.space/detect` or `https://YOUR-MODEL.onrender.com/detect`
   - `VITE_STREAM_API_KEY` = your Stream key *(only for video calls/chat)*
   - `VITE_API_URL` = `https://YOUR-BACKEND.onrender.com/api` *(only for video calls/chat)*
4. Deploy, then open `https://YOUR-APP.onrender.com/translator` on your phone *and* laptop.
   The Render rewrite in `render.yaml` keeps refreshing `/translator` working.
5. Put this URL in the model API's `ALLOWED_ORIGINS`.

## 4. Call backend (optional — only for video calls & chat) → Render
1. Render → **New Web Service** → your repo → Root Directory `backend` → Build `npm install` → Start `npm start`.
2. Env: `STREAM_API_KEY`, `STREAM_API_SECRET`, `CORS_ORIGIN` = `https://YOUR-APP.onrender.com`.
3. Free Render services sleep; open `/health` a minute before demoing.

## 5. Public GitHub repo
```bash
cd Gestura
git init && git add . && git commit -m "Fluent Meet: sign language to speech translator"
git branch -M main
git remote add origin https://github.com/YOU/REPO.git && git push -u origin main
```
Never commit `.env` files (only `.env.example`). Make the repo **Public** in Settings.

## 6. Fallback if Wi-Fi or the Space misbehaves during the demo
Run everything on your laptop (works offline once the weights are downloaded):
```bash
cd Model && pip install -r requirements.txt && python -m uvicorn api:app --app-dir src --port 7860
cd Frontend && echo "VITE_DETECT_URL=http://localhost:7860/detect" > .env && npm install && npm run dev
```
Open `http://localhost:5173/translator`.
