# Add more signs (runbook)

The detector only recognises signs it was trained on, so new signs need **new labelled images and a short
fine-tune**. The code is ready for it: translations for 9 more signs already exist, and one command keeps
`config.json` and the frontend in sync.

## Plan against the deadline (8:00 PM IST)
| Step | Time | Cut-off |
| --- | --- | --- |
| 1. Capture images | ~20 min | — |
| 2. Label (the slow part) | 60–90 min | **Start training by ~4:30 PM** |
| 3. Fine-tune on a GPU (Colab T4 is fine) | 45–60 min | Stop by ~5:45 PM |
| 4. Evaluate + deploy | 45 min | **Not deployed and checked by ~6:30 PM → ship the 3-sign version** |

A working 3-sign demo beats a broken 8-sign one. Keep the current deployment untouched until the new weights are proven.

## Which signs
Pick handshapes that look **clearly different** from each other and from the existing three
(`hello` salute, `iloveyou`, `thankyou` flat hand). Recommended five:

| Sign | Handshape | Spoken as |
| --- | --- | --- |
| `stop` | open palm facing the camera | "Stop" |
| `yes` | closed fist | "Yes" |
| `good` | thumbs up | "Good" |
| `ok` | thumb and index finger in a circle | "Okay" |
| `water` | "W" (three fingers up) near the chin | "I need water" |

Also prepared (translations exist, add if time allows): `no`, `help`, `please`, `sorry`. Avoid pairs that are
the same hand shape in a different place (e.g. `yes` fist vs `sorry` fist on the chest): one frame can't tell them apart.
These are ASL-style / common gestures; if you target Indian Sign Language, use ISL signs and add their
translations in `Frontend/src/lib/phrases.js`.

## 1. Register the signs
```bash
cd Model
python src/utils/add_signs.py stop yes good ok water
```
This appends to `src/config.json` (existing class ids unchanged) and updates `ACTIVE_SIGNS` in the frontend.
⚠️ From now on the **old weights no longer match `config.json`** — don't deploy this config without new weights.

## 2. Capture
```bash
pip uninstall -y opencv-python-headless && pip install opencv-python     # GUI build, once
python src/utils/collect_images.py --only stop yes good ok water --per-class 150 --delay 0.7 --out data/raw
```
Between bursts change what the model must not depend on: **background, lighting, distance, angle, left/right
hand, clothing — and ideally several people.** 150–200 per sign is a workable minimum. Also capture ~100
"negative" frames (no sign, hands down, talking) for the same reason — they stay unlabeled (empty label file).
Capture a few *separate sessions* for the test set; don't test on frames from the same burst you trained on.

## 3. Label
Label Studio → object detection → one rectangle around the hand per image → **export as YOLO**.
Class ids must follow `config.json` order: `hello=0, iloveyou=1, thankyou=2, stop=3, yes=4, good=5, ok=6, water=7`.
Keep your **existing** labelled data for the first three signs and put it in too — fine-tuning only on the new signs
makes the model forget the old ones.

Layout (≈85/15 train/test split by session):
```
Model/data/train/images  Model/data/train/labels
Model/data/test/images   Model/data/test/labels
```

## 4. Fine-tune (Colab T4 or any GPU)
```bash
pip install -r requirements-dev.txt albumentations scipy matplotlib
python src/train.py --resume pretrained/4426_model.pt --expand-head --device cuda --epochs 60
```
`--expand-head` keeps what the model learned for the 3 old signs and adds fresh outputs for the new ones.
Watch the first epoch time and set `--epochs` to fit your cut-off; `checkpoints/best_model.pt` is saved whenever the test loss improves.
If the loss barely moves for the new classes, try `--lr 5e-5`. (The weights file `pretrained/4426_model.pt` is
downloaded automatically the first time you run the API, or fetch it from `MODEL_URL` in `src/api.py`.)

## 5. Evaluate (these are the numbers for your README)
```bash
python src/evaluate.py --checkpoint checkpoints/best_model.pt --data data/test
```
Look at the confusion matrix: if two signs are confused, collect more varied images of those two.
`SCORE_THRESHOLD` (default 0.90) may be too strict for new signs — try 0.8 and compare false alarms.

## 6. Deploy
In your Hugging Face Space: upload `checkpoints/best_model.pt` into `pretrained/` (the web uploader handles the
large file), upload the updated `src/config.json`, and set the Space variable
`MODEL_PATH=/app/pretrained/best_model.pt`. **Weights and `config.json` must be updated together** or the API
fails at startup (class-count mismatch). Redeploy the frontend so its `ACTIVE_SIGNS` matches, then test `/translator`.

## 7. README
Paste the new `results/metrics.md`, update the sign list, and state how many images per sign you trained on.
Translations for Hindi, Marathi and Spanish were prepared quickly — have a native speaker glance at them before the demo.
