#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
command -v ffmpeg >/dev/null || { echo 'Install FFmpeg'; exit 1; }
command -v tesseract >/dev/null || { echo 'Install Tesseract OCR'; exit 1; }
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
if [ ! -f .env ]; then cp .env.example .env; echo 'Add AI_API_KEY to .env, then run again.'; exit 0; fi
uvicorn app.main:app --host 127.0.0.1 --port 8000
