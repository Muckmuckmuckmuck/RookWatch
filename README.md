# RookWatch — AI Work Verification (MVP)

Continuous video recording with AI analysis. Records what you're doing, every 15 min uploads the chunk to Google Gemini for analysis, returns dollar value, productivity score, and a full shift summary with charts.

---

## Two ways to run

**A) Local (laptop only)** — easiest for testing
**B) Hosted (live URL on your phone)** — for the demo

---

## Option A — Run Locally (5 min)

**1. Set API key in Terminal:**
```bash
export GOOGLE_API_KEY="paste_your_key_here"
```

**2. Navigate to the folder:**
```bash
cd ~/Desktop/rookwatch
```

**3. Make the script executable and run it:**
```bash
chmod +x start.sh && ./start.sh
```

**4. Open in Chrome:**
```
http://localhost:5000
```

---

## Option B — Host It On Render (free, gives you a real URL)

This gives you a public URL like `https://rookwatch.onrender.com` that works on any phone.

### Step 1 — Sign up for free GitHub if you don't have one
https://github.com/signup

### Step 2 — Upload to GitHub
1. Go to https://github.com/new
2. Name the repo `rookwatch`, click **Create repository**
3. Click **uploading an existing file**
4. Drag everything inside the `rookwatch` folder onto the page
5. Click **Commit changes**

### Step 3 — Sign up for Render
1. Go to https://render.com
2. Sign up with your GitHub account

### Step 4 — Deploy
1. Render dashboard → **New** → **Web Service**
2. Connect to your `rookwatch` repo
3. Render auto-detects `render.yaml` — click **Apply**
4. Find the **Environment Variables** section
5. Add `GOOGLE_API_KEY` = your actual key
6. Click **Create Web Service**
7. Wait 3-5 min for build to finish

### Step 5 — Use it
Render gives you a URL like `https://rookwatch-abc123.onrender.com`. Open on your phone, camera works, AI works.

**Note:** Free tier sleeps after 15 min of inactivity (~30 sec to wake). For demos, ping the URL a few minutes before.

---

## Option C — Quick ngrok Tunnel (no GitHub needed)

If you want to demo from your phone WITHOUT setting up Render:

**1. Run RookWatch locally** (Option A above)

**2. In a new Terminal:**
```bash
brew install ngrok
ngrok http 5000
```

**3. ngrok prints a URL like `https://abc123.ngrok-free.app`** — open that on your phone. Works as long as your laptop is running.

---

## How To Use

1. Open the page
2. Pick **1 min (testing)** in the dropdown for fast testing
3. Tap **Start Recording**
4. Do something for 30+ sec
5. Tap **↥ Submit Now** to upload immediately
6. Wait 15-30 sec for the chunk to appear with analysis
7. Scroll down to see:
   - **Productivity timeline** (% active per chunk over time)
   - **Shift summary** (AI narrative + score + highlights)
   - **Analyzed segments** (each chunk with tasks + dollar values)
8. Click **View Full Report** for the charts page
9. Tap **End Shift** when done

---

## What Each Button Does

| Button | What it does |
|---|---|
| Start Recording | Begin continuous capture |
| ↥ Submit Now | Upload current chunk early, start fresh chunk |
| ✓ End Shift | Upload final chunk and finish |
| ⟲ Flip | Switch front/back camera |
| ⇋ Mirror | Toggle horizontal mirroring |
| Audio toggle | Include audio in AI analysis |

---

## Cost
~$0.023 per 15-min chunk = $0.74 per 8-hour shift.

---

## Files

- `server.py` — Flask backend with Gemini integration
- `wsgi.py` — Production entry point
- `templates/index.html` — Recording page (video, charts, summary)
- `templates/report.html` — Full shift report
- `requirements.txt` — Python dependencies
- `render.yaml` — Render hosting config
- `start.sh` — Local startup script

---

## Troubleshooting

**Camera not available locally** — Allow camera in browser. On Chrome use `chrome://flags/#unsafely-treat-insecure-origin-as-secure` to allow `http://localhost:5000`. Or use ngrok for HTTPS.

**Render "Application failed"** — Check `GOOGLE_API_KEY` env var is set in Render dashboard.

**Camera not working on Render mobile** — Render gives you HTTPS automatically, so phone cameras should work. If denied, check phone Safari/Chrome camera permissions.
# RookWatch
