$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { throw 'FFmpeg missing. Install FFmpeg and add bin to PATH.' }
if (-not (Get-Command tesseract -ErrorAction SilentlyContinue) -and -not (Test-Path '.env')) { Write-Host 'Install Tesseract first: winget install --id UB-Mannheim.TesseractOCR -e' }
if (-not (Test-Path '.venv')) { py -3 -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path '.env')) { Copy-Item .env.example .env; Write-Host 'Add AI_API_KEY to .env, then run this script again.'; notepad .env; exit }
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
