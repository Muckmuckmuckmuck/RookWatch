# RookWatch · AI Work Verification (MVP)

A clip on camera and phone app concept that turns physical labor into a verified record of tasks done, with real time value attached. This repo contains the web MVP that powers the AI engine. The real product is the camera plus the phone app, which is what we are building next.

The web MVP records video continuously, uploads chunks every 15 minutes to Google Gemini for analysis, and returns a structured log of tasks performed, time spent, quality grades, and a dollar value per task. A manager dashboard surfaces all of it.

---

## Two ways to run

**A) Local (laptop only).** Easiest for testing.
**B) Hosted on Render (live URL on your phone).** For the demo.

---

## Option A · Run locally (5 min)

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

You will land on the pitch site. Click "Try the live demo" or go directly to `http://localhost:5000/demo` for the recording app.

---

## Option B · Host on Render (free, gives you a real URL)

This gives you a public URL like `https://rookwatch.onrender.com` that works on any phone.

### Step 1. Sign up for GitHub (free) if you do not have one
https://github.com/signup

### Step 2. Upload to GitHub
1. Go to https://github.com/new
2. Name the repo `rookwatch`, click **Create repository**
3. Click **uploading an existing file**
4. Drag everything inside the `rookwatch` folder onto the page
5. Click **Commit changes**

### Step 3. Sign up for Render
1. Go to https://render.com
2. Sign up with your GitHub account

### Step 4. Deploy
1. Render dashboard, **New**, **Web Service**
2. Connect to your `rookwatch` repo
3. Render auto-detects `render.yaml`, click **Apply**
4. Find the **Environment Variables** section
5. Add `GOOGLE_API_KEY` with your actual key
6. Click **Create Web Service**
7. Wait 3 to 5 min for build to finish

### Step 5. Use it
Render gives you a URL like `https://rookwatch.onrender.com`. Open on your phone, camera works, AI works.

**Note:** Free tier sleeps after 15 min of inactivity (~30 sec to wake). For demos, ping the URL a few minutes before.

---

## Option C · Quick ngrok tunnel (no GitHub needed)

If you want to demo from your phone WITHOUT setting up Render:

**1. Run RookWatch locally** (Option A above)

**2. In a new Terminal:**
```bash
brew install ngrok
ngrok http 5000
```

**3. ngrok prints a URL like `https://abc123.ngrok-free.app`.** Open that on your phone. Works as long as your laptop is running.

---

## Routes

- `/` Pitch site for investors and visitors
- `/demo` Recording app (the live AI engine proof of concept)
- `/report` Full shift report with charts
- `/health` Liveness check
- `/status` Current session state (JSON)

---

## How to use the live demo

1. Open the pitch site, click **Try the live demo**
2. Pick **1 min (testing)** in the dropdown for fast testing
3. Tap **Start Recording**
4. Do something for 30+ sec
5. Tap **Submit Now** to upload immediately
6. Wait 15 to 30 sec for the chunk to appear with analysis
7. Scroll down to see:
   - Productivity timeline (% active per chunk over time)
   - Shift summary (AI narrative + score + highlights)
   - Analyzed segments (each chunk with tasks + dollar values)
8. Click **View Full Report** for the charts page
9. Tap **End Shift** when done

---

## What each button does

| Button | What it does |
|---|---|
| Start Recording | Begin continuous capture |
| Submit Now | Upload current chunk early, start fresh chunk |
| End Shift | Upload final chunk and finish |
| Flip | Switch front/back camera |
| Mirror | Toggle horizontal mirroring |
| Audio toggle | Include audio in AI analysis |

---

## Cost

About $0.023 per 15-min chunk. About $0.74 per 8-hour shift, all in.

---

## Files

- `server.py` Flask backend with Gemini integration
- `wsgi.py` Production entry point
- `templates/pitch.html` Investor pitch site (homepage)
- `templates/index.html` Recording app (live demo)
- `templates/report.html` Full shift report
- `requirements.txt` Python dependencies
- `render.yaml` Render hosting config
- `start.sh` Local startup script

---

## Troubleshooting

**Camera not available locally.** Allow camera access in browser. On Chrome use `chrome://flags/#unsafely-treat-insecure-origin-as-secure` to allow `http://localhost:5000`. Or use ngrok for HTTPS.

**Render "Application failed".** Check `GOOGLE_API_KEY` env var is set in Render dashboard.

**Camera not working on Render mobile.** Render gives you HTTPS automatically, so phone cameras should work. If denied, check phone Safari or Chrome camera permissions.
