# Running VideoMind AI on Windows 11

## Prerequisites
1. Install Python 3.11+: https://www.python.org/downloads/windows/
2. Install FFmpeg and FFprobe. Add the FFmpeg `bin` folder to PATH. Verify `ffmpeg -version` and `ffprobe -version`.
3. Install local OCR engine: `winget install --id UB-Mannheim.TesseractOCR -e`. Reopen PowerShell and verify `tesseract --version`.
4. Obtain a Coarena API key. Do not share it in chat or commit it to GitHub.

If Tesseract is outside PATH, set `TESSERACT_CMD` in `.env` to its full executable path.

## Install and configure
1. Clone/download this repository and open PowerShell in its root folder.
2. Run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\run-windows.ps1
```

The first run creates `.venv`, installs Python dependencies, creates `.env`, opens it in Notepad, then exits.

Set:

```dotenv
AI_BASE_URL=https://coarena.ai/api/v1
AI_API_KEY=YOUR_COARENA_KEY
AI_MODEL=gemini-3-8-flash
FRAME_INTERVAL_SECONDS=1
FRAME_CHANGE_THRESHOLD=1.5
MAX_VIDEO_MINUTES=120
```

Use `gemini-4-carbon` if preferred. Keep `.env` private.

## Start
Run `.\run-windows.ps1` again. Open http://127.0.0.1:8000. Keep PowerShell open while processing.

## Analyze
1. Upload a video or provide a public YouTube URL.
2. Optionally add an SRT/VTT transcript.
3. Read the cloud data-retention notice. Selected screenshots and OCR text containing code are sent to Coarena. The original video is not uploaded by this app.
4. Confirm consent and start analysis.
5. Download the reconstructed project ZIP when complete.

## Local engines
- FFmpeg extracts timestamp-labelled frames.
- The local image-difference detector compares grayscale pixels and edge maps, retaining changed editor states against the last selected frame.
- Tesseract OCR runs locally on retained frames and extracts text, confidence and word coordinates.
- OCR is supporting evidence; the vision model must verify code against screenshots.

## Output
The ZIP contains reconstructed source files and `VIDEOMIND_MANIFEST.json`. Missing/unreadable lines are explicit placeholders. Review all files before running them. Results depend on resolution, readable line numbers, editor zoom and sampling interval.

## Troubleshooting
- FFmpeg missing: add its `bin` folder to PATH and reopen PowerShell.
- Tesseract missing: install it with winget, reopen PowerShell, verify `tesseract --version`; set `TESSERACT_CMD` if needed.
- API error: check key, model access and base URL in `.env`.
- Poor capture: use higher-resolution video and visible line numbers. Lowering sampling interval increases processing time and API usage.
- Stop server: press Ctrl+C in PowerShell.
