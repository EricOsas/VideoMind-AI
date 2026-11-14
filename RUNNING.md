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
SCENE_CHANGE_THRESHOLD=0.25
MAX_VIDEO_MINUTES=120
```

Use `gemini-4-carbon` if preferred. Keep `.env` private. Lower scene threshold detects more cuts and may increase vision API usage.

## Start
Run `.\run-windows.ps1` again. Open http://127.0.0.1:8000. Keep PowerShell open while processing.

## Analyze
1. Upload a video or provide a public YouTube URL.
2. Optionally set a focused range using start/end seconds. Leave defaults to analyze the full video.
3. Optionally add an SRT/VTT transcript. Transcript processing is unchanged.
4. Read the cloud data-retention notice. Selected screenshots and OCR text containing code are sent to Coarena. The original video is not uploaded by this app.
5. Confirm consent and start analysis.
6. Download the reconstructed project ZIP or the separate Markdown/JSON analysis report.

## Local analysis
- FFmpeg extracts timestamp-labelled frames in the selected range.
- FFmpeg scene-change detection identifies major visual transitions. The existing local pixel/edge difference detector remains active.
- Tesseract OCR runs locally on retained frames and extracts text, confidence and word coordinates.
- OCR is supporting evidence; the vision model must verify code against screenshots.

## Structured reports
The project ZIP includes:
- `VIDEOMIND_ANALYSIS_REPORT.md`: readable summary of range, scene timestamps, reconstructed files, observed/missing lines and confidence counts.
- `VIDEOMIND_ANALYSIS_REPORT.json`: machine-readable report with the same core analysis data.
- `VIDEOMIND_MANIFEST.json`: project file and missing-line manifest.

Missing/unreadable lines are explicit placeholders, not inferred code. Review all files before running them. Results depend on resolution, readable line numbers, editor zoom and sampling interval.

## Troubleshooting
- FFmpeg missing: add its `bin` folder to PATH and reopen PowerShell.
- Tesseract missing: install it with winget, reopen PowerShell, verify `tesseract --version`; set `TESSERACT_CMD` if needed.
- API error: check key, model access and base URL in `.env`.
- Poor capture: use higher-resolution video and visible line numbers. Lowering sampling interval increases processing time and API usage.
- Too many scene checkpoints: increase `SCENE_CHANGE_THRESHOLD` slightly.
- Stop server: press Ctrl+C in PowerShell.
