# 🎙️ Video Highlight AI — Podcast_VH

> **AI-driven multimodal video highlight generator for content repurposing.**  
> Drop in any podcast or talking-head video — get back a Short, a Highlight reel, and an Intro hook. Automatically.

![Python](https://img.shields.io/badge/python-3.10-blue?style=flat-square)
![Status](https://img.shields.io/badge/status-active%20development-orange?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![FFmpeg](https://img.shields.io/badge/requires-FFmpeg-red?style=flat-square)

---

## 📌 What it does

Takes any podcast or talking-head video and automatically generates three clip types:

| Output | Duration | Format | Platform |
|--------|----------|--------|----------|
| **Shorts**     | 30–60s | Vertical 9:16 | YouTube Shorts, Instagram Reels, TikTok |
| **Highlights** | 60–180s | Horizontal 16:9 | YouTube, repurposed content |
| **Intro**      | 25–40s | Horizontal 16:9 | Hook clip for audience capture |

---

## ⚙️ How it works

```
┌─────────────────────────────────────────────────────────────────┐
│                        VIDEO INPUT                              │
│              (local file or YouTube URL)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                   ┌──────────────────┐
                   │ Audio Extraction │  ← FFmpeg
                   └────────┬─────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │   Transcription  │  ← OpenAI Whisper
                   └────────┬─────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │   Segmentation   │  ← Sentence boundaries
                   └────────┬─────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  AUDIO   │ │   TEXT   │ │  VIDEO   │
        │ Scoring  │ │ Scoring  │ │ Scoring  │
        │          │ │          │ │          │
        │ • Energy │ │ •Keywords│ │ • Scenes │
        │ • Pitch  │ │ •Sentiment│ │ • Faces  │
        │ • Pauses │ │ • Hook   │ │          │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             └────────────┼────────────┘
                          ▼
                ┌──────────────────┐
                │  Score Fusion    │  ← Weighted multimodal
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │  Clip Selection  │
                └────────┬─────────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
        ┌──────────┐ ┌──────────┐ ┌───────┐
        │  Shorts  │ │Highlights│ │ Intro │
        │   9:16   │ │  16:9   │ │ 16:9  │
        └──────────┘ └──────────┘ └───────┘
                         │
                         ▼
          Face-Aware Crop + Crossfade Transitions
                         │
                         ▼
                    OUTPUT CLIP
```

---

## 🧠 Signals used

| Domain | Feature | Description |
|--------|---------|-------------|
| **Audio** | RMS Energy | Detects high-energy, loud moments |
| **Audio** | Pitch Variation (PYIN) | Flags expressive vocal delivery |
| **Audio** | Pause Detection | Identifies natural sentence boundaries |
| **Text**  | Keyword Density | Scores segments by topic relevance |
| **Text**  | Sentiment | Prefers emotionally charged language |
| **Text**  | Hook Score | Detects opener-style phrasing |
| **Video** | Scene Change Detection | Identifies visual cuts and transitions |
| **Video** | Face Presence + Position | Ensures face is centered before cropping |

---

## 🚀 Usage

```bash
# Generate a Short (30–60s vertical 9:16)
python main.py --input data/raw_videos/video.mp4 --mode shorts

# Generate a Highlight reel (60–180s horizontal 16:9)
python main.py --input data/raw_videos/video.mp4 --mode highlights

# Generate an Intro hook clip (25–40s)
python main.py --input data/raw_videos/video.mp4 --mode intro

# Pull directly from YouTube
python main.py --input https://youtube.com/watch?v=XXX --mode shorts
```

---

## 🛠️ Installation

### Prerequisites

- Python 3.10
- [FFmpeg](https://ffmpeg.org/download.html) — must be on your `PATH`
- CUDA-compatible GPU recommended (for Whisper)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/SurendraReddy7468/Video-Highlight-AI.git
cd Podcast_VH

# 2. Create and activate the environment
conda create -n Podcast_VH python=3.10
conda activate Podcast_VH

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify FFmpeg is accessible
ffmpeg -version
```

> **Windows users:** Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html), extract it, and add the `bin/` folder to your system `PATH`.

---

## 📁 Project structure

```
Podcast_VH/
│
├── main.py                         # Entry point — CLI interface
├── requirements.txt
├── data/
│   ├── raw_videos/                 # Drop input videos here
│   └── outputs/                    # Generated clips saved here
│
└── src/
    ├── pipeline.py                 # Full orchestration logic
    │
    ├── preprocessing/
    │   ├── video_loader.py
    │   ├── audio_extractor.py
    │   └── segmenter.py
    │
    ├── analysis/
    │   ├── audio/
    │   │   ├── energy.py           # RMS energy scoring
    │   │   ├── pitch.py            # PYIN pitch variation
    │   │   └── pause_detection.py
    │   │
    │   ├── text/
    │   │   ├── transcription.py    # Whisper integration
    │   │   ├── keywords.py
    │   │   ├── sentiment.py
    │   │   └── hook_detector.py
    │   │
    │   └── video/
    │       ├── scene_change.py
    │       └── face_detect.py
    │
    ├── scoring/
    │   └── highlight_score.py      # Multimodal score fusion
    │
    └── editing/
        ├── clip_generator.py
        └── format_converter.py     # Face-aware 16:9 → 9:16 crop
```

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `openai-whisper` | Speech-to-text transcription |
| `librosa` | Audio analysis (RMS, PYIN) |
| `transformers` | Sentiment analysis |
| `opencv-python` | Face detection, scene change |
| `ffmpeg-python` | Video/audio processing |
| `yt-dlp` | YouTube video download |
| `torch` | Model inference backend |

> Full list in [`requirements.txt`](requirements.txt)

---

## 🗺️ Roadmap

- [x] Audio feature extraction (RMS, Pitch, Pauses)
- [x] Whisper transcription + segmentation
- [x] Text scoring (keywords, sentiment, hooks)
- [x] Face-aware format conversion
- [x] Crossfade transitions
- [ ] **LLM-powered intro selection** (Claude API)
- [ ] B-roll detection and filtering
- [ ] Auto-subtitle overlay
- [ ] Thumbnail generation
- [ ] Web interface 

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

---

## 📄 License

[MIT](LICENSE)