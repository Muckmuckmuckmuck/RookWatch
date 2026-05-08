"""
RookWatch MVP — Continuous video recording + 15-min auto-batch analysis
Single-worker prototype optimized for laptop browser testing.
"""
import os
import json
import re
import threading
import time
import tempfile
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from google import genai
from google.genai import types

# ============================================================
#  Set GOOGLE_API_KEY env var or paste key below
#  Get one free at: https://aistudio.google.com/app/apikey
API_KEY = os.environ.get("GOOGLE_API_KEY", "PASTE_YOUR_API_KEY_HERE")
# ============================================================

# Pricing for cost estimation (Gemini 2.5 Flash-Lite, $0.10/1M input tokens)
# Video: 258 tokens per second of video at 1fps sampling
COST_PER_1M_TOKENS = 0.10
VIDEO_TOKENS_PER_SEC = 258
AUDIO_TOKENS_PER_SEC = 25

# Industry-realistic HOURLY wage rates ($/hour) for each task type.
# Task value = (hourly_rate / 3600) × duration_seconds
# These reflect actual labor market rates, not arbitrary per-task amounts.
TASK_HOURLY_RATES = {
    # Skilled trades (high)
    "welding": 65, "operating machinery": 55, "wiring": 60, "electrical": 60,
    "plumbing": 55, "framing": 38,
    # Semi-skilled construction
    "installing": 35, "drilling": 32, "assembling": 32, "nailing": 28,
    "hammering": 28, "cutting": 30, "measuring": 25, "painting": 28,
    "inspecting": 35, "digging": 22,
    # General labor (low)
    "carrying": 18, "lifting": 18, "cleaning": 16,
    # Service work
    "took order": 18, "served": 18, "handed": 16, "wiped": 15,
    "bagged": 15, "scanned": 16, "restocked": 17, "rang up": 18,
    # Office / knowledge work
    "typed": 30, "wrote": 30, "drafted": 35, "reviewed": 32, "annotated": 28,
    "highlighted": 25, "studied": 25,
    # Reading / studying (low — passive activity)
    "read": 22, "flipped page": 15, "page": 18,
    # Healthcare
    "charted": 45, "took blood pressure": 40, "administered": 55,
    # Default for unknown tasks
    "default": 20
}

# Minimum task duration in seconds — anything shorter gets rounded up to this for value calc
MIN_TASK_DURATION = 3

app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200MB max upload (covers 15-min 720p chunks)

client = None
if API_KEY and API_KEY != "PASTE_YOUR_API_KEY_HERE":
    client = genai.Client(api_key=API_KEY)

# ---- Single-worker session state (MVP) ----
session = {
    "shift_start": None,        # datetime when first chunk arrived
    "shift_ended": False,
    "chunks": [],               # list of analyzed chunk results
    "total_value": 0.0,
    "total_cost": 0.0,
    "total_video_seconds": 0,
    "audio_enabled": False,
}
lock = threading.Lock()


def estimate_cost(duration_seconds, audio_enabled):
    """Estimate API cost for a video chunk."""
    video_tokens = duration_seconds * VIDEO_TOKENS_PER_SEC
    audio_tokens = duration_seconds * AUDIO_TOKENS_PER_SEC if audio_enabled else 0
    total_tokens = video_tokens + audio_tokens
    return (total_tokens / 1_000_000) * COST_PER_1M_TOKENS


def get_hourly_rate(task):
    """Look up the hourly wage rate for a task description."""
    tl = (task or "").lower()
    for kw, rate in TASK_HOURLY_RATES.items():
        if kw in tl:
            return rate
    return TASK_HOURLY_RATES["default"]


def calculate_task_value(task_name, duration_seconds):
    """Calculate dollar value as (hourly_rate / 3600) × seconds, with a minimum floor."""
    hourly = get_hourly_rate(task_name)
    effective_seconds = max(duration_seconds, MIN_TASK_DURATION)
    return round((hourly / 3600.0) * effective_seconds, 2)


def analyze_video_chunk(file_path, duration_seconds, audio_enabled, chunk_index):
    """Send video to Gemini and get structured work analysis."""
    if client is None:
        return {
            "error": "API key not configured",
            "summary": "Configuration required",
            "tasks": [],
            "total_value": 0,
            "quality": "unknown",
            "duration_seconds": duration_seconds,
        }

    try:
        # Upload video file to Gemini
        uploaded = client.files.upload(file=file_path)

        # Wait for processing
        max_wait = 60
        elapsed = 0
        while uploaded.state.name == "PROCESSING" and elapsed < max_wait:
            time.sleep(2)
            elapsed += 2
            uploaded = client.files.get(name=uploaded.name)

        if uploaded.state.name == "FAILED":
            return {"error": "Video processing failed on Gemini side"}

        prompt = f"""You are an AI work tracker analyzing a {duration_seconds:.0f}-second video clip of a person.

Your job is to detect EVERY observable action they performed and log it as a discrete task — no matter how small.

This applies to ANY job category:
- Manual labor: "Hammered nail into board", "Sawed wood plank", "Carried supplies"
- Service work: "Took customer order", "Handed customer drink", "Wiped down table"
- Office/study: "Read page of book", "Flipped page", "Typed paragraph", "Wrote in notebook"
- Healthcare: "Took patient blood pressure", "Adjusted IV", "Charted notes"
- Retail: "Scanned item", "Bagged groceries", "Restocked shelf"
- Anything else observable: ANY discrete action counts

{"You can hear audio. Use spoken context (e.g. 'taking your order', 'I'm done', 'next page') to identify tasks more accurately." if audio_enabled else "Video only — no audio analysis available."}

CRITICAL RULES:
1. Log every distinct action — even small ones like "flipped page" or "moved cup"
2. Use the visible action verbs — be SPECIFIC about what was done
3. If you see ANY observable action, the worker is "active" — don't mark idle just because work seems light
4. For a {duration_seconds:.0f}-second clip, expect to log multiple distinct tasks
5. Estimate task durations realistically — most micro-actions are 3-15 seconds

Return ONLY valid JSON, no markdown, no preamble:

{{
  "summary": "2-3 sentence overview of what activity happened in this clip",
  "tasks": [
    {{
      "name": "Specific action verb + object (e.g. 'Read page of book', 'Hammered nail', 'Took customer order')",
      "start_time": "MM:SS timestamp when task started in the clip",
      "duration_seconds": estimated_seconds_for_this_task,
      "category": "construction" | "service" | "office" | "study" | "healthcare" | "retail" | "general" | "other",
      "quality": "excellent" | "standard" | "needs_attention",
      "details": "Brief description of what specifically was done and any notable context"
    }}
  ],
  "active_seconds": total_seconds_actively_doing_something,
  "idle_seconds": total_seconds_completely_still_or_off_camera,
  "overall_quality": "excellent" | "standard" | "needs_attention",
  "flags": ["only include if there are real safety/quality concerns"],
  "notable_moments": ["interesting observations like 'completed reading chapter 3'"]
}}

If the video shows ANY person doing ANY action, you MUST return at least one task. Empty tasks array is only acceptable if the clip is genuinely empty (no person, black screen, etc)."""

        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=[uploaded, prompt],
        )

        # Cleanup uploaded file from Gemini
        try:
            client.files.delete(name=uploaded.name)
        except Exception:
            pass

        text = (response.text or "").strip()

        # Strip code fences
        if "```" in text:
            text = text.split("```")[1].replace("json", "", 1).strip()
            if "```" in text:
                text = text.split("```")[0].strip()

        # Find JSON object
        if not text.startswith("{"):
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end > start:
                text = text[start:end + 1]

        result = json.loads(text)

        # Compute dollar value for each task using realistic hourly rates
        chunk_value = 0.0
        for task in result.get("tasks", []):
            duration = task.get("duration_seconds", 5)
            task_value = calculate_task_value(task.get("name", ""), duration)
            task["dollar_value"] = task_value
            task["hourly_rate"] = get_hourly_rate(task.get("name", ""))
            chunk_value += task_value

        result["total_value"] = round(chunk_value, 2)
        result["chunk_index"] = chunk_index
        result["duration_seconds"] = duration_seconds
        result["analyzed_at"] = datetime.now().strftime("%I:%M:%S %p")

        return result

    except json.JSONDecodeError as e:
        return {
            "error": f"Could not parse AI response: {str(e)[:100]}",
            "summary": "AI returned invalid format",
            "tasks": [],
            "total_value": 0,
            "duration_seconds": duration_seconds,
        }
    except Exception as e:
        return {
            "error": str(e)[:200],
            "summary": "Analysis failed",
            "tasks": [],
            "total_value": 0,
            "duration_seconds": duration_seconds,
        }


# ─── ROUTES ────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/report")
def report():
    return render_template("report.html")


@app.route("/upload_chunk", methods=["POST"])
def upload_chunk():
    """Receive video chunk, send to Gemini, store result."""
    if "video" not in request.files:
        return jsonify({"error": "No video file in request"}), 400

    video_file = request.files["video"]
    duration = float(request.form.get("duration_seconds", 0) or 0)
    audio_on = request.form.get("audio_enabled", "false").lower() == "true"
    is_final = request.form.get("is_final", "false").lower() == "true"
    is_manual = request.form.get("is_manual", "false").lower() == "true"

    if duration < 1:
        return jsonify({"error": "Video too short (less than 1 second)"}), 400

    # Save to temp file (Gemini SDK needs a file path)
    tmp = tempfile.NamedTemporaryFile(suffix=".webm", delete=False)
    video_file.save(tmp.name)
    tmp.close()

    try:
        with lock:
            if session["shift_start"] is None:
                session["shift_start"] = datetime.now()
            session["audio_enabled"] = audio_on
            chunk_index = len(session["chunks"]) + 1

        cost = estimate_cost(duration, audio_on)
        result = analyze_video_chunk(tmp.name, duration, audio_on, chunk_index)
        result["estimated_cost"] = round(cost, 6)
        result["audio_enabled"] = audio_on
        result["is_manual"] = is_manual
        result["is_final"] = is_final
        result["timestamp"] = datetime.now().strftime("%I:%M:%S %p")

        with lock:
            session["chunks"].append(result)
            session["total_value"] += result.get("total_value", 0)
            session["total_cost"] += cost
            session["total_video_seconds"] += duration
            if is_final:
                session["shift_ended"] = True

        return jsonify({
            "success": True,
            "chunk": result,
            "session_total_value": round(session["total_value"], 2),
            "session_total_cost": round(session["total_cost"], 6),
            "chunk_count": len(session["chunks"]),
        })

    finally:
        # Always delete temp video
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


@app.route("/status")
def status():
    """Return current session state."""
    with lock:
        return jsonify({
            "shift_start": session["shift_start"].isoformat() if session["shift_start"] else None,
            "shift_ended": session["shift_ended"],
            "total_value": round(session["total_value"], 2),
            "total_cost": round(session["total_cost"], 6),
            "total_video_seconds": session["total_video_seconds"],
            "chunk_count": len(session["chunks"]),
            "audio_enabled": session["audio_enabled"],
            "chunks": session["chunks"],
        })


@app.route("/reset", methods=["POST"])
def reset():
    with lock:
        session["shift_start"] = None
        session["shift_ended"] = False
        session["chunks"] = []
        session["total_value"] = 0.0
        session["total_cost"] = 0.0
        session["total_video_seconds"] = 0
    return jsonify({"success": True})


@app.route("/shift_summary")
def shift_summary():
    """Generate an AI narrative summarizing the entire shift across all chunks."""
    with lock:
        chunks = list(session["chunks"])
        total_value = session["total_value"]
        total_secs = session["total_video_seconds"]
        shift_start = session["shift_start"]

    if not chunks:
        return jsonify({"summary": "No work recorded yet. Start recording to generate a shift summary."})

    if client is None:
        return jsonify({"summary": "API key not configured."})

    # Build a compact representation of all chunks for the LLM
    chunk_lines = []
    for i, c in enumerate(chunks, 1):
        if c.get("error"):
            continue
        tasks_summary = "; ".join([
            f"{t.get('name','?')} ({t.get('duration_seconds',0)}s)"
            for t in c.get("tasks", [])[:6]
        ])
        chunk_lines.append(
            f"Chunk {i} ({c.get('duration_seconds',0):.0f}s): {c.get('summary','')} | Tasks: {tasks_summary}"
        )

    if not chunk_lines:
        return jsonify({"summary": "All chunks failed to analyze. Check API connection."})

    chunks_text = "\n".join(chunk_lines)
    duration_min = total_secs / 60

    prompt = f"""Below is a series of analyzed video chunks from a worker's shift. Produce a polished, professional shift summary report.

SHIFT FACTS:
- Total recorded: {duration_min:.1f} minutes ({len(chunks)} chunks)
- Total value generated: ${total_value:.2f}

CHUNK BREAKDOWN:
{chunks_text}

Return ONLY valid JSON, no markdown:
{{
  "headline": "One-sentence headline summarizing the whole shift",
  "narrative": "2-3 paragraph professional narrative describing what got done, in chronological flow",
  "highlights": ["3-5 specific accomplishments worth calling out"],
  "productivity_score": "0-100 score with brief reason",
  "improvement_areas": ["constructive suggestions for next shift, if any"]
}}"""

    try:
        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=[prompt]
        )
        text = (response.text or "").strip()
        if "```" in text:
            text = text.split("```")[1].replace("json", "", 1).strip()
            if "```" in text:
                text = text.split("```")[0].strip()
        if not text.startswith("{"):
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end > start:
                text = text[start:end + 1]
        return jsonify(json.loads(text))
    except Exception as e:
        return jsonify({
            "headline": "Shift complete",
            "narrative": f"Recorded {len(chunks)} chunks totaling {duration_min:.0f} minutes. Analysis summary unavailable: {str(e)[:100]}",
            "highlights": [],
            "productivity_score": "—",
            "improvement_areas": []
        })


@app.route("/health")
def health():
    return jsonify({
        "ok": True,
        "model_ready": client is not None,
        "chunks_analyzed": len(session["chunks"]),
    })


if __name__ == "__main__":
    print("\n" + "═" * 60)
    print("  WORKVERIFY MVP — Continuous Video Analysis")
    print("═" * 60)
    print(f"\n  💻  Recording  → http://localhost:5000")
    print(f"  📊  Report     → http://localhost:5000/report")
    print(f"  🩺  Health     → http://localhost:5000/health")
    print(f"\n  Model: gemini-2.5-flash-lite-preview-06-17")
    print(f"  Auto-upload every: 15 minutes (configurable in UI)")
    print("═" * 60 + "\n")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
