# Setup Guide for Teammates

## Step 1 — Prerequisites
- Install Python 3.10: https://www.python.org/downloads/
- Install FFmpeg:
  - Windows: winget install Gyan.FFmpeg
  - Then verify: ffmpeg -version (should print version, not error)

## Step 2 — Clone the repo
git clone https://github.com/SurendraReddy7468/Video-Highlight-AI.git
cd Video-Highlight-AI

## Step 3 — Create environment (use conda)
conda create -n Podcast_VH python=3.10
conda activate Podcast_VH

## Step 4 — Install packages
pip install -r requirements.txt

## Step 5 — Test it works (no video needed)
python test_stage1.py

## Step 6 — Run on sample video
python main.py --input data/raw_videos/PUT_A_VIDEO_HERE.mp4 --mode shorts

## Common errors
| Error | Fix |
|-------|-----|
| ffmpeg not found | Re-install FFmpeg and restart terminal |
| torch not installed | pip install torch --index-url https://download.pytorch.org/whl/cpu |
| ModuleNotFoundError | Make sure conda env is activated |
