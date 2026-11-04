# Deploy in ~30 minutes

Order matters: model API first (the frontend needs its URL), then the frontend, then (optional) the call backend.

## 1. Model API → Hugging Face Space (free CPU)
1. huggingface.co → **New Space** → SDK **Docker** → blank template → public.
2. Upload the **contents of the `Model/` folder** to the Space (drag-and-drop in the web UI, or `git push`).
   `Model/README.md` already carries the Space settings (port 7860). Don't upload `data/` or `checkpoints/`.
3. The first start builds the image (~5–10 min) and downloads the weights.
4. Space → **Settings → Variables**: `ALLOWED_ORIGINS` = `https://YOUR-APP.vercel.app,http://localhost:5173`
   (add it again after you know the Vercel URL; the Space restarts).
5. Check: open `https://<user>-<space>.hf.space/health` → `{"status":"ok","model_loaded":true}`.

> The app's built-in default model URL points at someone else's Space whose CORS list won't include *your* site.
> Always set `VITE_DETECT_URL` to your own Space.

## 2. Frontend → Vercel
1. vercel.com → **Add New Project** → import your GitHub repo → **Root Directory: `Frontend`** (Vite is auto-detected).
2. Environment variables (set **before** the first build — Vite bakes them in):
   - `VITE_DETECT_URL` = `https://<user>-<space>.hf.space/detect`
   - `VITE_STREAM_API_KEY` = your Stream key *(only for video calls/chat)*
   - `VITE_API_URL` = `https://YOUR-BACKEND.onrender.com/api` *(only for video calls/chat)*
3. Deploy, then open `https://YOUR-APP.vercel.app/translator` on your phone *and* laptop.
   (`Frontend/vercel.json` already rewrites all paths, so refreshing `/translator` works.)
4. Go back to step 1.4 and put this URL in `ALLOWED_ORIGINS`.

## 3. Call backend (optional — only for video calls & chat) → Render
1. Render → **New Web Service** → your repo → Root Directory `backend` → Build `npm install` → Start `npm start`.
2. Env: `STREAM_API_KEY`, `STREAM_API_SECRET`, `CORS_ORIGIN` = `https://YOUR-APP.vercel.app`.
3. Free Render services sleep; open `/health` a minute before demoing.

## 4. Public GitHub repo
```bash
cd Sign-detection-main
git init && git add . && git commit -m "Fluent Meet: sign language to speech translator"
git branch -M main
git remote add origin https://github.com/YOU/REPO.git && git push -u origin main
```
Never commit `.env` files (only `.env.example`). Make the repo **Public** in Settings.

## 5. Fallback if Wi-Fi or the Space misbehaves during the demo
Run everything on your laptop (works offline once the weights are downloaded):
```bash
cd Model && pip install -r requirements.txt && uvicorn api:app --app-dir src --port 7860
cd Frontend && echo "VITE_DETECT_URL=http://localhost:7860/detect" > .env && npm install && npm run dev
```
Open `http://localhost:5173/translator`.
