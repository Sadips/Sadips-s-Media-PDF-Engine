import os
import io
import shutil
import subprocess
import uuid
from pathlib import Path
import fitz  # PyMuPDF
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB limit

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)

VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm', 'flv', 'wmv', 'm4v'}
PDF_EXTENSIONS = {'pdf'}
ALLOWED_EXTENSIONS = VIDEO_EXTENSIONS | PDF_EXTENSIONS

def get_ffmpeg_path():
    """Dynamically locate the FFmpeg executable."""
    ffmpeg_in_path = shutil.which("ffmpeg")
    if ffmpeg_in_path:
        return ffmpeg_in_path

    # Specific WinGet package path fallback
    winget_dir = Path(os.path.expanduser("~")) / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    if winget_dir.exists():
        matches = list(winget_dir.rglob("ffmpeg.exe"))
        if matches:
            return str(matches[0])
            
    return "ffmpeg"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def purge_uploads_folder():
    """Safety helper to clean up remaining temp files in upload folder."""
    for p in UPLOAD_FOLDER.glob("*"):
        if p.is_file():
            try:
                p.unlink()
            except Exception:
                pass

def compress_pdf_file(input_path: Path, output_path: Path):
    """Compress PDF document using PyMuPDF stream optimization and garbage collection without file locks."""
    pdf_bytes = input_path.read_bytes()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    doc.save(
        str(output_path),
        garbage=4,
        deflate=True,
        clean=True
    )
    doc.close()

def compress_video_file(input_path: Path, output_path: Path):
    """Compress video using FFmpeg engine with x264 CRF 28 Fast Preset."""
    ffmpeg_bin = get_ffmpeg_path()
    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", str(input_path),
        "-c:v", "libx264",
        "-crf", "28",
        "-preset", "fast",
        str(output_path)
    ]
    process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {process.stderr[-400:] if process.stderr else 'Unknown error'}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/compress', methods=['POST'])
def compress_file():
    purge_uploads_folder()  # Ensure zero leftover files exist

    if 'file' not in request.files:
        return jsonify({'error': 'No file field provided in request.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for upload.'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'Unsupported file format. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    original_filename = secure_filename(file.filename)
    filename_stem = Path(original_filename).stem
    ext = Path(original_filename).suffix.lower().lstrip('.')
    
    file_id = str(uuid.uuid4())[:8]
    input_path = UPLOAD_FOLDER / f"{file_id}_{original_filename}"

    try:
        # 1. Save uploaded file to server temp folder
        file.save(str(input_path))

        # 2. Smart Routing based on file extension
        if ext in PDF_EXTENSIONS:
            compressed_name = f"{filename_stem}_compressed.pdf"
            mimetype = 'application/pdf'
            output_path = UPLOAD_FOLDER / f"{file_id}_{compressed_name}"
            compress_pdf_file(input_path, output_path)

        elif ext in VIDEO_EXTENSIONS:
            compressed_name = f"{filename_stem}_compressed.mp4"
            mimetype = 'video/mp4'
            output_path = UPLOAD_FOLDER / f"{file_id}_{compressed_name}"
            compress_video_file(input_path, output_path)

        else:
            return jsonify({'error': 'Unsupported file type'}), 400

        # 3. Read compressed output into memory buffer & trigger immediate disk deletion
        with open(output_path, 'rb') as f:
            compressed_data = f.read()

        # Immediate cleanup of both input and output files from disk
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()

        # 4. Stream compressed buffer to client with download trigger
        return send_file(
            io.BytesIO(compressed_data),
            as_attachment=True,
            download_name=compressed_name,
            mimetype=mimetype
        )

    except Exception as e:
        if input_path.exists():
            try:
                input_path.unlink()
            except Exception:
                pass
        if 'output_path' in locals() and output_path.exists():
            try:
                output_path.unlink()
            except Exception:
                pass
        return jsonify({'error': f'Compression error: {str(e)}'}), 500

if __name__ == '__main__':
    purge_uploads_folder()
    print(f"FFmpeg binary detected at: {get_ffmpeg_path()}")
    app.run(host='127.0.0.1', port=5000, debug=True)
