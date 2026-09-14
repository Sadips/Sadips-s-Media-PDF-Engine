import os
import io
import shutil
import subprocess
import uuid
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB limit

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)

VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm', 'flv', 'wmv', 'm4v'}
PDF_EXTENSIONS = {'pdf'}
IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff'}
ALLOWED_EXTENSIONS = VIDEO_EXTENSIONS | PDF_EXTENSIONS | IMAGE_EXTENSIONS

MIME_TYPES = {
    'pdf': 'application/pdf',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'webp': 'image/webp',
    'bmp': 'image/bmp',
    'tiff': 'image/tiff'
}

def get_ffmpeg_path():
    """Dynamically locate the FFmpeg executable."""
    ffmpeg_in_path = shutil.which("ffmpeg")
    if ffmpeg_in_path:
        return ffmpeg_in_path

    winget_dir = Path(os.path.expanduser("~")) / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    if winget_dir.exists():
        matches = list(winget_dir.rglob("ffmpeg.exe"))
        if matches:
            return str(matches[0])
            
    return "ffmpeg"

def get_ffprobe_path():
    """Dynamically locate the FFprobe executable."""
    ffprobe_in_path = shutil.which("ffprobe")
    if ffprobe_in_path:
        return ffprobe_in_path

    ffmpeg_bin = get_ffmpeg_path()
    if ffmpeg_bin and os.path.isabs(ffmpeg_bin):
        candidate = Path(ffmpeg_bin).parent / "ffprobe.exe"
        if candidate.exists():
            return str(candidate)

    return "ffprobe"

def get_video_duration(input_path: Path) -> float:
    """Extract video duration in seconds using ffprobe."""
    ffprobe_bin = get_ffprobe_path()
    cmd = [
        ffprobe_bin,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprintwrappers=1:nokey=1",
        str(input_path)
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(res.stdout.strip())
    except Exception:
        return 0.0

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

def compress_image_file(input_path: Path, output_path: Path, target_kb: float = None):
    """Compress image using Pillow with optional target KB size reduction loop."""
    target_bytes = (target_kb * 1024) if target_kb else None

    with Image.open(input_path) as original_img:
        ext = output_path.suffix.lower().lstrip('.')
        img = original_img.copy()

        # Convert RGBA/P to RGB for JPEG
        if ext in ('jpg', 'jpeg') and img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGB')

        # Auto mode: Default quality 75 optimization
        if not target_bytes:
            save_kwargs = {'optimize': True}
            if ext in ('jpg', 'jpeg', 'webp'):
                save_kwargs['quality'] = 75
            elif ext == 'png':
                save_kwargs['compress_level'] = 6
            img.save(str(output_path), **save_kwargs)
            return

        # Target KB Mode: Iterative Quality & Dimension Scale Reduction Loop
        quality = 85
        scale = 1.0

        while True:
            current_width = int(img.width * scale)
            current_height = int(img.height * scale)
            
            if scale < 1.0:
                resized_img = img.resize((max(1, current_width), max(1, current_height)), Image.Resampling.LANCZOS)
            else:
                resized_img = img

            save_kwargs = {'optimize': True}
            if ext in ('jpg', 'jpeg', 'webp'):
                save_kwargs['quality'] = quality
            elif ext == 'png':
                save_kwargs['compress_level'] = 9

            resized_img.save(str(output_path), **save_kwargs)
            current_size = output_path.stat().st_size

            # Check if target KB reached or lower limits hit
            if current_size <= target_bytes or (quality <= 15 and scale <= 0.2):
                break

            # Reduce quality first down to 15, then scale down image dimensions
            if quality > 15:
                quality -= 15
            else:
                scale *= 0.8

def compress_pdf_file(input_path: Path, output_path: Path, target_kb: float = None):
    """Compress PDF document using PyMuPDF stream optimization and downsampling."""
    target_bytes = (target_kb * 1024) if target_kb else None

    pdf_bytes = input_path.read_bytes()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # Initial Pass: Maximum stream optimization and garbage collection
    doc.save(
        str(output_path),
        garbage=4,
        deflate=True,
        clean=True
    )

    if target_bytes and output_path.stat().st_size > target_bytes:
        # Pass 2: Downsample embedded page images if size exceeds target KB
        for page in doc:
            image_list = page.get_images(full=True)
            for img_info in image_list:
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                if base_image:
                    image_bytes = base_image["image"]
                    try:
                        with Image.open(io.BytesIO(image_bytes)) as pil_img:
                            if pil_img.mode in ('RGBA', 'P', 'LA'):
                                pil_img = pil_img.convert('RGB')
                            
                            # Reduce image resolution and quality to meet target KB
                            pil_img.thumbnail((pil_img.width // 2, pil_img.height // 2))
                            out_io = io.BytesIO()
                            pil_img.save(out_io, format="JPEG", quality=40, optimize=True)
                            
                            # Replace image stream in PDF page
                            page.replace_image(xref, stream=out_io.getvalue())
                    except Exception:
                        pass

        # Re-save with updated downsampled images
        doc.save(
            str(output_path),
            garbage=4,
            deflate=True,
            clean=True
        )

    doc.close()

def compress_video_file(input_path: Path, output_path: Path, target_kb: float = None):
    """Compress video using FFmpeg engine with CRF or dynamic bitrate calculation."""
    ffmpeg_bin = get_ffmpeg_path()

    # Auto Mode: CRF 28 Fast Preset
    if not target_kb:
        cmd = [
            ffmpeg_bin,
            "-y",
            "-i", str(input_path),
            "-c:v", "libx264",
            "-crf", "28",
            "-preset", "fast",
            str(output_path)
        ]
    else:
        # Target KB Mode: Calculate Video Bitrate = (Target Size in kilobits / Duration in sec) - Audio Bitrate
        duration = get_video_duration(input_path)
        if duration <= 0:
            duration = 10.0  # Fallback duration if unprobed

        audio_bitrate_kbps = 64
        total_target_bits = target_kb * 8 * 1024
        total_bitrate_bps = total_target_bits / duration
        video_bitrate_kbps = int((total_bitrate_bps / 1000) - audio_bitrate_kbps)

        cmd = [ffmpeg_bin, "-y", "-i", str(input_path), "-c:v", "libx264"]

        if video_bitrate_kbps < 50:
            # Low bitrate: apply scale filter and set minimum 40k video bitrate
            video_bitrate_kbps = max(30, video_bitrate_kbps)
            cmd.extend(["-vf", "scale=-2:480"])

        cmd.extend([
            "-b:v", f"{video_bitrate_kbps}k",
            "-c:a", "aac",
            "-b:a", f"{audio_bitrate_kbps}k",
            "-preset", "fast",
            str(output_path)
        ])

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

    # Parse target KB parameter
    target_kb_raw = request.form.get('target_kb', 'auto')
    target_kb = None
    if target_kb_raw and target_kb_raw != 'auto':
        try:
            target_kb = float(target_kb_raw)
        except ValueError:
            target_kb = None

    original_filename = secure_filename(file.filename)
    filename_stem = Path(original_filename).stem
    ext = Path(original_filename).suffix.lower().lstrip('.')
    
    file_id = str(uuid.uuid4())[:8]
    input_path = UPLOAD_FOLDER / f"{file_id}_{original_filename}"

    try:
        # 1. Save uploaded file to server temp folder
        file.save(str(input_path))

        # 2. Tri-Engine Smart Routing based on file extension
        if ext in IMAGE_EXTENSIONS:
            compressed_name = f"{filename_stem}_compressed.{ext}"
            mimetype = MIME_TYPES.get(ext, 'image/jpeg')
            output_path = UPLOAD_FOLDER / f"{file_id}_{compressed_name}"
            compress_image_file(input_path, output_path, target_kb=target_kb)

        elif ext in PDF_EXTENSIONS:
            compressed_name = f"{filename_stem}_compressed.pdf"
            mimetype = 'application/pdf'
            output_path = UPLOAD_FOLDER / f"{file_id}_{compressed_name}"
            compress_pdf_file(input_path, output_path, target_kb=target_kb)

        elif ext in VIDEO_EXTENSIONS:
            compressed_name = f"{filename_stem}_compressed.mp4"
            mimetype = 'video/mp4'
            output_path = UPLOAD_FOLDER / f"{file_id}_{compressed_name}"
            compress_video_file(input_path, output_path, target_kb=target_kb)

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
