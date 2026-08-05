# 🚀 Production Deployment Commands Guide

This guide provides deployment commands for running the **Media & PDF Compression Web Application** in production environments.

---

## 🌐 Option 1: Render.com Deployment (Recommended)

Render.com supports 1-click containerized deployment using the included [render.yaml](file:///C:/Users/user\.gemini\antigravity-ide\scratch\video_compressor_app\render.yaml) and [Dockerfile](file:///C:/Users/user\.gemini\antigravity-ide\scratch\video_compressor_app\Dockerfile).

### Steps to Deploy on Render:

1. **Push your code to GitHub / GitLab**:
   ```bash
   git init
   git add .
   git commit -m "Deploy Media & PDF Compressor"
   git remote add origin https://github.com/YOUR_USERNAME/video_compressor_app.git
   git push -u origin main
   ```

2. **Deploy via Render Dashboard**:
   - Go to **[dashboard.render.com](https://dashboard.render.com)**.
   - Click **New +** -> **Web Service**.
   - Connect your GitHub repository.
   - Select **Docker** as the Runtime (Render will automatically detect your `Dockerfile` and install FFmpeg + Python).
   - Click **Create Web Service**.

> Render will automatically build the container and provide your live HTTPS URL (e.g. `https://media-pdf-compressor.onrender.com`).

---

## 💻 Option 2: Windows Production Server (Waitress WSGI)

```powershell
cd C:\Users\user\.gemini\antigravity-ide\scratch\video_compressor_app
.\.venv\Scripts\python.exe -m pip install waitress
.\.venv\Scripts\python.exe -m waitress --port=5000 app:app
```

---

## 🐧 Option 3: Linux Server Deployment (Gunicorn WSGI)

```bash
sudo apt update && sudo apt install -y ffmpeg
pip install -r requirements.txt gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 300 app:app
```

---

## 🐳 Option 4: Docker Container Deployment

```bash
docker build -t media-pdf-compressor .
docker run -d -p 5000:5000 --name compressor-app media-pdf-compressor
```

---

## ☁️ Option 5: Google Cloud Run Deployment

```bash
gcloud run deploy video-compressor \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 600
```
