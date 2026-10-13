"""
Multimodal Processing Module for Truthify-AI.

Supports:
- PDF Documents: Text extraction, document structure, page count, metadata (using pypdf).
- Images: EXIF metadata extraction, manipulation signal detection, and OCR / vision analysis (using PIL, pytesseract, optional Gemini Vision).
- Videos: Frame extraction, duration & resolution calculation, chyron/banner OCR across keyframes (using OpenCV cv2).
"""

import base64
import io
import logging
import os
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)

# Check for pypdf
try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False
    logger.warning("pypdf is not installed. PDF text extraction will be disabled.")

# Check for PIL
try:
    from PIL import Image, ExifTags
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logger.warning("PIL (Pillow) is not installed. Image processing will be limited.")

# Check for OpenCV
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logger.warning("OpenCV (cv2) is not installed. Video frame extraction will be disabled.")

# Check for pytesseract
try:
    import pytesseract
    # Configure Windows common default paths if tesseract is not in system PATH
    tesseract_candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for candidate in tesseract_candidates:
        if os.path.exists(candidate):
            pytesseract.pytesseract.tesseract_cmd = candidate
            break
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False

# Check for Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def detect_media_type(filename: str = "", mime_type: str = "") -> str:
    """Determine media type based on filename extension or MIME type."""
    ext = Path(filename).suffix.lower() if filename else ""
    mime = (mime_type or "").lower()

    if ext == ".pdf" or "pdf" in mime:
        return "pdf"
    if ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff"] or "image" in mime:
        return "image"
    if ext in [".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"] or "video" in mime:
        return "video"
    return "text"


def extract_from_pdf(source: Union[bytes, str, Path]) -> dict:
    """Extract text and metadata from a PDF file."""
    if not HAS_PYPDF:
        return {
            "text": "",
            "error": "pypdf library not available.",
            "pages": 0,
            "metadata": {}
        }

    try:
        if isinstance(source, (str, Path)):
            reader = pypdf.PdfReader(str(source))
        else:
            reader = pypdf.PdfReader(io.BytesIO(source))

        num_pages = len(reader.pages)
        page_texts = []
        for i, page in enumerate(reader.pages):
            txt = page.extract_text() or ""
            if txt.strip():
                page_texts.append(f"--- Page {i+1} ---\n{txt.strip()}")

        extracted_text = "\n\n".join(page_texts)

        meta = {}
        if reader.metadata:
            meta = {
                "title": reader.metadata.title or "",
                "author": reader.metadata.author or "",
                "subject": reader.metadata.subject or "",
                "creator": reader.metadata.creator or "",
            }

        return {
            "text": extracted_text,
            "pages": num_pages,
            "metadata": meta,
            "is_scanned": len(extracted_text.strip()) < 50 and num_pages > 0
        }
    except Exception as e:
        logger.error(f"Error parsing PDF: {e}")
        return {
            "text": "",
            "error": str(e),
            "pages": 0,
            "metadata": {}
        }


def _run_local_ocr(image: Image.Image) -> str:
    """Run local OCR via pytesseract if available."""
    if not HAS_PYTESSERACT:
        return ""
    try:
        return pytesseract.image_to_string(image).strip()
    except Exception:
        return ""


def _call_gemini_vision(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """Call Gemini API for vision understanding if GEMINI_API_KEY is configured."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return ""
    try:
        import httpx
        b64_data = base64.b64encode(image_bytes).decode("utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
        payload = {
            "contents": [{
                "parts": [
                    {
                        "text": (
                            "Extract all readable text, headlines, banners, and claims from this image. "
                            "Also describe what is depicted and state any visible signs of digital alteration or manipulation."
                        )
                    },
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64_data
                        }
                    }
                ]
            }]
        }
        resp = httpx.post(url, json=payload, timeout=20.0)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
    except Exception as e:
        logger.warning(f"Gemini Vision call failed: {e}")
    return ""


def extract_from_image(source: Union[bytes, str, Path], filename: str = "") -> dict:
    """Extract metadata, EXIF, and text from an image."""
    if not HAS_PIL:
        return {
            "text": "",
            "metadata": {},
            "error": "Pillow (PIL) library not available."
        }

    try:
        raw_bytes = None
        if isinstance(source, (str, Path)):
            with open(source, "rb") as f:
                raw_bytes = f.read()
            img = Image.open(source)
        else:
            raw_bytes = source
            img = Image.open(io.BytesIO(source))

        width, height = img.size
        img_format = img.format or "Unknown"

        # EXIF analysis
        exif_data = {}
        try:
            raw_exif = img.getexif()
            if raw_exif:
                for tag_id, val in raw_exif.items():
                    tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                    # Convert bytes to string if needed
                    if isinstance(val, bytes):
                        try:
                            val = val.decode("utf-8", errors="ignore")
                        except Exception:
                            val = str(val)
                    if isinstance(val, (str, int, float)):
                        exif_data[tag_name] = str(val)[:100]
        except Exception:
            pass

        # Text extraction (OCR or Gemini Vision)
        extracted_text = ""
        ocr_source = "none"

        # Try Gemini Vision if key configured
        if os.getenv("GEMINI_API_KEY") and raw_bytes:
            mime = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
            gemini_text = _call_gemini_vision(raw_bytes, mime)
            if gemini_text:
                extracted_text = gemini_text
                ocr_source = "gemini_multimodal"

        # Try local pytesseract if Gemini didn't return text
        if not extracted_text:
            local_ocr = _run_local_ocr(img)
            if local_ocr:
                extracted_text = local_ocr
                ocr_source = "pytesseract"

        # Generate lightweight thumbnail base64 for frontend preview
        thumb_b64 = ""
        try:
            thumb = img.copy()
            thumb.thumbnail((320, 320))
            buf = io.BytesIO()
            thumb.convert("RGB").save(buf, format="JPEG", quality=75)
            thumb_b64 = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
        except Exception:
            pass

        return {
            "text": extracted_text,
            "ocr_source": ocr_source,
            "metadata": {
                "dimensions": f"{width}x{height}",
                "format": img_format,
                "has_exif": bool(exif_data),
                "camera_model": exif_data.get("Model", ""),
                "software_used": exif_data.get("Software", ""),
                "datetime_original": exif_data.get("DateTime", ""),
            },
            "thumbnail_b64": thumb_b64,
        }
    except Exception as e:
        logger.error(f"Error parsing image: {e}")
        return {
            "text": "",
            "error": str(e),
            "metadata": {}
        }


def extract_from_video(source_path: str, max_frames: int = 5) -> dict:
    """
    Extract video metadata and sample keyframes using OpenCV.
    Performs OCR across keyframes to capture banners, chyrons, and on-screen claims.
    """
    if not HAS_CV2:
        return {
            "text": "",
            "metadata": {},
            "error": "OpenCV (cv2) not available."
        }

    try:
        cap = cv2.VideoCapture(str(source_path))
        if not cap.isOpened():
            return {
                "text": "",
                "error": "Could not open video file.",
                "metadata": {}
            }

        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        duration_sec = round(total_frames / fps, 2) if fps > 0 else 0

        # Sample keyframe timestamps
        frame_indices = []
        if total_frames > 0:
            step = max(1, total_frames // (max_frames + 1))
            frame_indices = [step * (i + 1) for i in range(max_frames)]

        extracted_texts = []
        thumbnail_b64 = ""

        for idx, frame_no in enumerate(frame_indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            # First keyframe serves as preview thumbnail
            if not thumbnail_b64:
                try:
                    small = cv2.resize(frame, (320, int(320 * height / width))) if width > 0 else frame
                    _, buf = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    thumbnail_b64 = f"data:image/jpeg;base64,{base64.b64encode(buf.tobytes()).decode('utf-8')}"
                except Exception:
                    pass

            # Run OCR on frame if pytesseract available
            if HAS_PYTESSERACT and HAS_PIL:
                try:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb)
                    frame_txt = pytesseract.image_to_string(pil_img).strip()
                    if frame_txt and len(frame_txt) > 5:
                        time_stamp = round(frame_no / fps, 1)
                        extracted_texts.append(f"[Frame @ {time_stamp}s]: {frame_txt}")
                except Exception:
                    pass

        cap.release()

        combined_text = "\n".join(extracted_texts)
        if not combined_text:
            combined_text = (
                f"Video media analyzed: duration {duration_sec}s ({total_frames} frames @ {round(fps, 1)} FPS, {width}x{height}). "
                "No high-contrast text overlay detected in sampled keyframes."
            )

        return {
            "text": combined_text,
            "metadata": {
                "duration_seconds": duration_sec,
                "fps": round(fps, 2),
                "total_frames": total_frames,
                "resolution": f"{width}x{height}",
                "keyframes_sampled": len(frame_indices),
            },
            "thumbnail_b64": thumbnail_b64,
        }
    except Exception as e:
        logger.error(f"Error parsing video: {e}")
        return {
            "text": "",
            "error": str(e),
            "metadata": {}
        }


def process_media_file(
    file_bytes: Optional[bytes] = None,
    file_path: Optional[str] = None,
    filename: str = "",
    mime_type: str = ""
) -> dict:
    """
    Unified entrypoint to process an uploaded media file (PDF, Image, Video, or Text).
    Returns extracted text, media metadata, and thumbnail preview.
    """
    media_type = detect_media_type(filename, mime_type)

    if media_type == "pdf":
        source = file_path if file_path else file_bytes
        res = extract_from_pdf(source)
        return {
            "media_type": "pdf",
            "filename": filename,
            "extracted_text": res.get("text", ""),
            "metadata": {
                "pages": res.get("pages", 0),
                **res.get("metadata", {})
            },
            "thumbnail_b64": "",
        }

    elif media_type == "image":
        source = file_path if file_path else file_bytes
        res = extract_from_image(source, filename=filename)
        return {
            "media_type": "image",
            "filename": filename,
            "extracted_text": res.get("text", ""),
            "metadata": res.get("metadata", {}),
            "thumbnail_b64": res.get("thumbnail_b64", ""),
            "ocr_source": res.get("ocr_source", "none"),
        }

    elif media_type == "video":
        if file_path:
            res = extract_from_video(file_path)
        elif file_bytes:
            # Write to a temporary file for OpenCV VideoCapture
            import tempfile
            ext = Path(filename).suffix or ".mp4"
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            try:
                res = extract_from_video(tmp_path)
            finally:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
        else:
            res = {"text": "", "metadata": {}}

        return {
            "media_type": "video",
            "filename": filename,
            "extracted_text": res.get("text", ""),
            "metadata": res.get("metadata", {}),
            "thumbnail_b64": res.get("thumbnail_b64", ""),
        }

    else:
        # Default text
        text_content = ""
        if file_bytes:
            try:
                text_content = file_bytes.decode("utf-8", errors="ignore")
            except Exception:
                pass
        return {
            "media_type": "text",
            "filename": filename,
            "extracted_text": text_content,
            "metadata": {},
            "thumbnail_b64": "",
        }
