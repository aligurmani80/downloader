@echo off
title NexaLoad - Universal Video & Audio Downloader
echo ========================================================
echo   NexaLoad Universal Video & Audio Downloader
echo ========================================================
echo Starting FastAPI Backend + Frontend at http://localhost:8000 ...
cd backend
venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
