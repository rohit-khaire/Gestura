# Demo & pitch guide (3 minutes)

## Before you go on (do these once)
- [ ] Open `/translator` on the deployed URL, start the camera, test **in the room's lighting** against a plain background.
- [ ] Browser: Chrome or Edge. Volume up. Click once on the page first (browsers block audio until a click).
- [ ] Open the page in a second window/phone for the "in a call" moment (optional, needs Stream keys).
- [ ] Have the **simulated signs** buttons ready as a safety net if Wi-Fi or the model API hiccups — and say so honestly if you use them.
- [ ] Keep `Model/results/metrics.md` open to quote real numbers.

## Script
**0:00 – Problem (20 s).** "India's health ministry cites about 63 million people with significant hearing impairment — an older survey, but the official figure. Almost no one around them signs. A doctor's visit or a video call becomes a barrier. We built a bridge." (Say "official estimate", not "today's exact number".)

**0:20 – Live sign → speech (50 s).** Sign *hello*, then *thank you*. Pause. "It waited for a pause, built a sentence, and spoke it." Point at the live text. Switch language to Hindi, sign again: "Same sign, spoken in the listener's language."

**1:10 – Speech → captions (25 s).** Turn on Live captions; a teammate speaks. "The other direction: speech becomes text for the deaf user. Two-way."

**1:35 – Why it's reliable (40 s).** "A detector flickers frame to frame. We added a voting window so a sign must win 3 of 5 frames, holding a sign says it once, and words are grouped into sentences." Show the test suite (`npm test`, 14 passing) and the confusion matrix.

**2:15 – Numbers (20 s).** Quote mAP, per-sign F1 and latency from `metrics.md` — only numbers you actually measured.

**2:35 – Limits & next (25 s).** "Three static signs today. Next: Indian Sign Language vocabulary and a landmark-plus-temporal model for moving signs." Naming limits yourself earns trust.

## Likely judge questions
- **Why DETR?** End-to-end detection without hand-tuned NMS; small variant (1+1 layers) runs on CPU.
- **How do you stop false triggers?** Vote window, de-duplication, confidence threshold 0.90.
- **Privacy?** Frames are sent to the model API only while detection is on; nothing is stored. Speech uses the browser's own engine.
- **Scalability?** Stateless API; translation logic runs in the browser, so adding users doesn't add server state.
- **What did you build during the hackathon?** Be precise and truthful (see checklist below).

## Submission checklist (deadline: **4 Nov 2026, 8:00 PM IST**)
- [ ] GitHub repo is **public**; README TODOs filled (team, members, links, screenshots, metrics, AI disclosure, credits)
- [ ] `Model/results/metrics.md` pasted into the README
- [ ] Live link works from a fresh browser / phone
- [ ] Model API `ALLOWED_ORIGINS` includes your deployed frontend URL
- [ ] Commit history shows the work done during the 48 hours
- [ ] Submitted once, before the deadline (late entries are not accepted)
