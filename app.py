"""
Podcast VH — Local Demo Server
Run: python app.py
Open: http://localhost:5000
"""

import os
import sys
import json
import time
import threading
import traceback
from pathlib import Path
from flask import (
    Flask, request, jsonify, render_template,
    send_file, Response, stream_with_context
)
from werkzeug.utils import secure_filename

# ── Make sure src/ is importable ──────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024  # 2 GB max upload

UPLOAD_FOLDER  = "data/raw_videos"
OUTPUT_FOLDERS = {
    "shorts":     "data/outputs/shorts",
    "highlights": "data/outputs/highlights",
    "intro":      "data/outputs/intro",
}
ALLOWED_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}

# Global job store: job_id -> {status, steps, output_path, error}
JOBS = {}


def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def make_job_id():
    return f"job_{int(time.time() * 1000)}"


# ── Progress-aware pipeline runner ────────────────────────────────────────────

def run_pipeline_job(job_id, source, mode, whisper_model="base"):
    """
    Run the full pipeline in a background thread.
    Updates JOBS[job_id] at each stage so the frontend can poll progress.
    """
    JOBS[job_id] = {
        "status": "running",
        "current_step": 0,
        "steps": [
            {"num": 1, "label": "Load Video",      "status": "waiting"},
            {"num": 2, "label": "Extract Audio",   "status": "waiting"},
            {"num": 3, "label": "Transcribe",       "status": "waiting"},
            {"num": 4, "label": "Segment",          "status": "waiting"},
            {"num": 5, "label": "Score Segments",   "status": "waiting"},
            {"num": 6, "label": "Generate Clip",    "status": "waiting"},
            {"num": 7, "label": "Convert Format",   "status": "waiting"},
        ],
        "output_path": None,
        "error": None,
        "created_at": time.time(),
    }

    def set_step(n, status):
        JOBS[job_id]["steps"][n - 1]["status"] = status
        JOBS[job_id]["current_step"] = n

    try:
        # ── Import all modules ────────────────────────────────────────────────
        from src.preprocessing.video_loader    import load_video
        from src.preprocessing.audio_extractor import extract_audio
        from src.analysis.text.transcription   import transcribe_audio
        from src.preprocessing.segmenter       import merge_segments, save_segments
        from src.scoring.highlight_score        import score_segments, save_scores
        from src.editing.clip_generator         import generate_clip, generate_intro_clip
        from src.editing.format_converter       import convert_to_vertical, convert_to_horizontal

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        for folder in OUTPUT_FOLDERS.values():
            os.makedirs(folder, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(
            source if not source.startswith("http") else "youtube_video"
        ))[0]
        timestamp = int(time.time())

        # ── STEP 1: Load video ────────────────────────────────────────────────
        set_step(1, "running")
        video_path = load_video(source, UPLOAD_FOLDER)
        set_step(1, "done")

        # Update base_name from actual downloaded file
        base_name = os.path.splitext(os.path.basename(video_path))[0]

        # ── STEP 2: Extract audio ─────────────────────────────────────────────
        set_step(2, "running")
        audio_path = extract_audio(video_path)
        set_step(2, "done")

        # ── STEP 3: Transcribe ────────────────────────────────────────────────
        set_step(3, "running")
        raw_segments = transcribe_audio(audio_path, model_size=whisper_model)
        set_step(3, "done")

        # ── STEP 4: Segment ───────────────────────────────────────────────────
        set_step(4, "running")
        segments = merge_segments(raw_segments)
        save_segments(segments, name=base_name)
        set_step(4, "done")

        # ── STEP 5: Score ─────────────────────────────────────────────────────
        set_step(5, "running")
        scored = score_segments(segments, audio_path, video_path, mode="podcast")
        save_scores(scored)
        set_step(5, "done")

        # ── STEP 6: Generate clip ─────────────────────────────────────────────
        set_step(6, "running")
        out_dir = OUTPUT_FOLDERS.get(mode, OUTPUT_FOLDERS["shorts"])

        if mode == "intro":
            raw_clip = generate_intro_clip(
                video_path, scored,
                output_dir=out_dir,
                output_name=f"{base_name}_intro_{timestamp}",
            )
            JOBS[job_id]["status"]      = "done"
            JOBS[job_id]["output_path"] = raw_clip
            set_step(6, "done")
            set_step(7, "done")
            return
        else:
            raw_clip, selected_segments = generate_clip(
                video_path, scored,
                mode=mode,
                output_dir=out_dir,
                output_name="raw_clip",
            )
        set_step(6, "done")

        # ── STEP 7: Format conversion ─────────────────────────────────────────
        set_step(7, "running")
        final_name = f"{base_name}_{mode}_{timestamp}.mp4"
        final_path = os.path.join(out_dir, final_name)

        if mode == "shorts":
            # Per-segment face positions for accurate speaker cropping
            per_segment_faces = []
            running = 0.0
            for seg in selected_segments:
                dur    = seg["end"] - seg["start"]
                face_x = seg.get("face_center_x", 0.5)
                per_segment_faces.append((running, running + dur, face_x))
                running += dur
            final_path = convert_to_vertical(
                raw_clip, final_path,
                per_segment_faces=per_segment_faces
            )
        else:
            final_path = convert_to_horizontal(raw_clip, final_path)

        # Clean up raw clip
        if os.path.exists(raw_clip) and raw_clip != final_path:
            try:
                os.remove(raw_clip)
            except Exception:
                pass

        set_step(7, "done")
        JOBS[job_id]["status"]      = "done"
        JOBS[job_id]["output_path"] = final_path

    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"[Job {job_id}] ERROR:\n{error_msg}")
        # Mark current running step as error
        for step in JOBS[job_id]["steps"]:
            if step["status"] == "running":
                step["status"] = "error"
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["error"]  = str(e)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    """
    Start a pipeline job. Accepts:
      - youtube_url (form field)  OR
      - file        (multipart upload)
      - mode        (shorts / highlights / intro)
      - whisper     (tiny / base / small)
    """
    mode    = request.form.get("mode", "shorts")
    whisper = request.form.get("whisper", "base")

    # Validate mode
    if mode not in ("shorts", "highlights", "intro"):
        return jsonify({"error": "Invalid mode"}), 400

    # Get source — priority: local path > YouTube URL > file upload
    local_path  = request.form.get("local_path", "").strip()
    youtube_url = request.form.get("youtube_url", "").strip()
    uploaded    = request.files.get("file")

    if local_path:
        # Local path — fastest for demo, no upload needed
        if not os.path.exists(local_path):
            return jsonify({"error": f"Local file not found: {local_path}"}), 400
        source = local_path
    elif youtube_url:
        source = youtube_url
    elif uploaded and uploaded.filename:
        if not allowed_file(uploaded.filename):
            return jsonify({"error": "Invalid file type. Use mp4, mov, avi, mkv or webm"}), 400
        filename = secure_filename(uploaded.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        uploaded.save(save_path)
        source = save_path
    else:
        return jsonify({"error": "Provide a local path, YouTube URL, or upload a video file"}), 400

    # Create job and start background thread
    job_id = make_job_id()
    thread = threading.Thread(
        target=run_pipeline_job,
        args=(job_id, source, mode, whisper),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def status(job_id):
    """Poll job status and step progress."""
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify({
        "status":       job["status"],
        "current_step": job["current_step"],
        "steps":        job["steps"],
        "error":        job["error"],
        "has_output":   job["output_path"] is not None,
    })


@app.route("/download/<job_id>")
def download(job_id):
    """Download the generated clip."""
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    if job["status"] != "done" or not job["output_path"]:
        return jsonify({"error": "Output not ready"}), 400

    output_path = job["output_path"]
    if not os.path.exists(output_path):
        return jsonify({"error": "Output file missing"}), 404

    return send_file(
        output_path,
        as_attachment=True,
        download_name=os.path.basename(output_path),
        mimetype="video/mp4",
    )


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Create required directories
    for folder in [UPLOAD_FOLDER, *OUTPUT_FOLDERS.values(), "data/audio",
                   "data/transcripts", "data/segments", "data/temp"]:
        os.makedirs(folder, exist_ok=True)

    print("\n" + "="*55)
    print("  🎙️  Podcast VH — Local Demo Server")
    print("  Open: http://localhost:5000")
    print("="*55 + "\n")
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)