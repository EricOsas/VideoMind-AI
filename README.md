# VideoMind AI

Local-first coding tutorial reconstruction for Windows 11. It extracts changing video frames, runs local Tesseract OCR and pixel/edge image-difference detection, then uses Coarena vision models to reconstruct source files into a downloadable project ZIP.

See [RUNNING.md](RUNNING.md) for complete setup and operating instructions.

## Requirements
- Python 3.11+
- FFmpeg and FFprobe on PATH
- Tesseract OCR on PATH
- Coarena API key

## Quick start
Install prerequisites, then run in PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\run-windows.ps1
```

Set `AI_API_KEY` in the generated `.env`, rerun the launcher, then open http://127.0.0.1:8000.

Default API: `https://coarena.ai/api/v1`
Default model: `gemini-3-8-flash` (or `gemini-4-carbon`).

The original video stays local. Selected screenshots and OCR text are sent to Coarena only after explicit consent. Review Coarena's data-retention terms before sending code screenshots.

The output ZIP contains reconstructed source files and `VIDEOMIND_MANIFEST.json`. Missing lines are marked, not fabricated. Review generated code before running it.
