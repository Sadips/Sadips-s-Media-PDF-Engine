# 🎥 Video Compression Web Application (Localhost Guide)

A high-performance, modular Video Compression Web Application built with **Python (Flask)**, **FFmpeg**, and a modern **Glassmorphic UI**.

> [!NOTE]  
> This project is a **Python Flask** application (uses `pip`, not `npm`).

---

## 🚀 Quick Start Guide (Localhost)

### 1. Prerequisites
- **Python 3.10+**
- **FFmpeg** (The application automatically detects FFmpeg from system `PATH` or Windows WinGet package locations).

### 2. Environment Setup

Open PowerShell or Command Prompt in the project folder:
```powershell
cd C:\Users\user\.gemini\antigravity-ide\scratch\video_compressor_app
```

Activate the pre-configured Python virtual environment:
```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Or run directly via venv python executable:
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Running the Web App on Localhost

Start the Flask local development server:
```powershell
.\.venv\Scripts\python.exe app.py
```

Once running, open your browser and go to:
👉 **[http://localhost:5000](http://localhost:5000)** or **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## ⚡ Features & Specs

| Feature | Details |
| :--- | :--- |
| **Backend Framework** | Python 3 + Flask 3.1 |
| **Video Engine** | FFmpeg Subprocess Execution |
| **Compression Codec** | `libx264` (H.264 / AVC) |
| **CRF Quality** | `28` |
| **FFmpeg Preset** | `fast` |
| **File Output** | `<original_filename>_compressed.mp4` |
| **Disk Cleanup** | In-memory stream buffer with **0 leftover server files** |
| **UI Aesthetics** | Glassmorphism, Antigravity Dark Theme, Progress Spinner |

---

## 📂 Project Structure

```
video_compressor_app/
├── app.py                     # Flask server & FFmpeg compression engine
├── requirements.txt           # Python dependency manifest
├── README.md                  # Localhost instructions
├── .venv/                     # Python virtual environment
├── uploads/                   # Temporary upload directory (auto-cleaned)
├── templates/
│   └── index.html             # Modular UI template
└── static/
    ├── css/
    │   └── style.css          # Glassmorphic Antigravity dark theme
    └── js/
        └── app.js             # Drag-and-drop & auto-download controller
```

---

## 🛡 Automatic Cleanup Mechanics

When a video is uploaded and compressed:
1. The backend streams the compressed file directly to the client browser.
2. Both the temporary uploaded file and compressed output file are **immediately unlinked and deleted from server storage**.
3. Zero storage accumulation occurs on localhost.
