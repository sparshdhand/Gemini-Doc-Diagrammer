# filename: app.py
import os
import tempfile
import uuid
import unicodedata
import re
from typing import Optional

from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Google AI Studio (Gemini) SDK
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

# PDF/DOCX text extraction
from pdfminer.high_level import extract_text as extract_pdf_text
from docx import Document

app = Flask(__name__)

# SECURITY: Read API key from environment. Never hardcode.
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "Missing GEMINI_API_KEY. Set it as an environment variable.\n"
        "macOS/Linux: export GEMINI_API_KEY='YOUR_API_KEY'\n"
        "Windows (PowerShell): setx GEMINI_API_KEY 'YOUR_API_KEY'"
    )

client = genai.Client(api_key=API_KEY)

DEFAULT_MODEL = "gemini-2.0-flash"

# Allowed file types and max size (e.g., 25 MB)
ALLOWED_EXTS = {"pdf", "docx"}
MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# Keep the system instruction ASCII-safe (avoid curly quotes)
SYSTEM_INSTRUCTION = (
    "Render an ascii diagram using a code block to explain the "
    "relationship between the classes and relevant moving parts of this "
    "document, their function, relationship to each other, etc. "
    "focus on any changes implied the document, highlighting what's new\n\n"
    "FORMAT:\n"
    "use familiar ascii characters. the result will be rendered in "
    "monospace. render a solid horizontal line comprised of 60 '_' "
    "characters across the first line and the last line of the document.\n\n"
    "cap every line to 60 characters.\n\n"
    "use an directory/hierarchy structure only if useful to explain files "
    "and relationships. otherwise opt for a flowchart / more visual style.\n\n"
    "If there is no document or content provided, ask for some"
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def allowed_file(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTS


def extract_docx_text(path: str) -> str:
    doc = Document(path)
    parts = []
    for p in doc.paragraphs:
        txt = (p.text or "").strip()
        if txt:
            parts.append(txt)
    # Include table text if any
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                cell_text = (cell.text or "").strip()
                if cell_text:
                    parts.append(cell_text)
    return "\n".join(parts)


SMART_CHARS_MAP = {
    "\u2018": "'",  # left single quote
    "\u2019": "'",  # right single quote
    "\u201C": '"',  # left double quote
    "\u201D": '"',  # right double quote
    "\u2013": "-",  # en dash
    "\u2014": "-",  # em dash
    "\u2026": "...",  # ellipsis
    "\u00A0": " ",   # non-breaking space
}

SMART_RE = re.compile("|".join(re.escape(k) for k in SMART_CHARS_MAP.keys()))


def normalize_text(s: str) -> str:
    """
    Normalize to NFC, replace smart quotes/dashes with ASCII,
    strip non-printable control chars (except newline, tab),
    and ensure the result is safe for HTTP headers/payloads.
    """
    if not s:
        return ""
    # Unicode normalization
    s = unicodedata.normalize("NFC", s)
    # Replace smart chars with ASCII equivalents
    s = SMART_RE.sub(lambda m: SMART_CHARS_MAP[m.group(0)], s)
    # Remove other control characters except \n and \t
    s = "".join(ch for ch in s if (ch == "\n" or ch == "\t" or (32 <= ord(ch) <= 126)))
    return s


@app.route("/", methods=["GET"])
def serve_index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """
    Multipart/form-data:
      - file: PDF or DOCX (required)
      - model: optional, default DEFAULT_MODEL
      - user_prompt: optional extra instruction
    Returns JSON with the model's ASCII response.
    """
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400

        filename = secure_filename(file.filename)
        if not allowed_file(filename):
            return jsonify({"error": "Unsupported file type. Use PDF or DOCX."}), 400

        model = request.form.get("model", DEFAULT_MODEL)
        user_prompt = request.form.get("user_prompt", "").strip()

        # Save to a secure temporary file
        tmpdir = tempfile.mkdtemp(prefix="upload_")
        ext = filename.rsplit(".", 1)[1].lower()
        local_name = f"{uuid.uuid4().hex}.{ext}"
        local_path = os.path.join(tmpdir, local_name)
        file.save(local_path)

        # Extract text
        try:
            if ext == "pdf":
                extracted_text = extract_pdf_text(local_path)
            else:
                extracted_text = extract_docx_text(local_path)
        except Exception as ex:
            # Clean up before returning
            try:
                os.remove(local_path)
                os.rmdir(tmpdir)
            except Exception:
                pass
            return jsonify({"error": "Failed to extract text", "details": str(ex)}), 400

        extracted_text = (extracted_text or "").strip()
        if not extracted_text:
            try:
                os.remove(local_path)
                os.rmdir(tmpdir)
            except Exception:
                pass
            return jsonify({"error": "No readable text found in document"}), 400

        # Optional truncation
        MAX_CHARS = 100_000
        if len(extracted_text) > MAX_CHARS:
            extracted_text = extracted_text[:MAX_CHARS] + "\n...[truncated]"

        # Normalize all text inputs to avoid Unicode header/payload issues
        norm_system = normalize_text(SYSTEM_INSTRUCTION)
        norm_user_prompt = normalize_text(user_prompt)
        norm_file_text = normalize_text(extracted_text)

        # Build contents
        contents = []
        if norm_system:
            contents.append(types.Content(role="user", parts=[types.Part(text=norm_system)]))
        if norm_user_prompt:
            contents.append(types.Content(role="user", parts=[types.Part(text=norm_user_prompt)]))
        formatted_text = f"file text:\n{norm_file_text}"
        contents.append(types.Content(role="user", parts=[types.Part(text=formatted_text)]))

        generation_config = types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=2048,
        )

        result = client.models.generate_content(
            model=model,
            contents=contents,
            config=generation_config,
        )

        # Extract text response
        text = ""
        if result and getattr(result, "candidates", None):
            for cand in result.candidates:
                if cand.content and cand.content.parts:
                    for part in cand.content.parts:
                        if getattr(part, "text", None):
                            text += part.text
            text = text.strip()

        # Clean up temp files
        try:
            os.remove(local_path)
            os.rmdir(tmpdir)
        except Exception:
            pass

        if not text:
            return jsonify({"error": "Empty response from model"}), 502

        return jsonify({
            "model": model,
            "filename": filename,
            "response": text
        })

    except genai_errors.APIError as e:
        # Correct exception class from google.genai.errors
        return jsonify({"error": "Gemini API error", "details": str(e)}), 502
    except UnicodeEncodeError as e:
        # Catch any residual encoding issues and report clearly
        return jsonify({"error": "Unicode encoding error", "details": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Server error", "details": str(e)}), 500


if __name__ == "__main__":
    # Run locally; use a WSGI server (gunicorn) behind a reverse proxy in prod.
    app.run(host="127.0.0.1", port=5000, debug=True)
