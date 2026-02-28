# Gemini Doc Diagrammer (Document Analyzer) — AI-Powered ASCII Diagrams

## ❌ PROJECT ARCHIVED

This project has been archived due to discontinuation of Gemini 2.0.

Transform PDF/DOCX documents into clear ASCII diagrams using Google AI Studio (Gemini). Upload a file, optionally add extra instructions, and get a formatted code block that visualizes classes, relationships, and changes—bounded by 60-underscore lines.

## Features
- Drag-and-drop upload for PDF and DOCX.
- Server-side text extraction (pdfminer.six, python-docx).
- Gemini backend via google-genai SDK.
- Enforced output format (code block, 60-character borders, 60-char line cap).
- Optional user instructions appended to system prompt.
- Simple Flask API and minimal frontend.

## Quick Start

### Prerequisites
- Python 3.10+ (tested on 3.11–3.14).
- A Google AI Studio API key (Gemini).

### Project Structure
```text
project/
├─ app.py
├─ requirements.txt
└─ static/
   └─ index.html
```

### Install
```bash
# From project root
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configure
```bash
# Set your Gemini API key
export GEMINI_API_KEY="YOUR_KEY"      # macOS/Linux
# PowerShell (new terminal required after this):
setx GEMINI_API_KEY "YOUR_KEY"
```

### Run
```bash
python app.py
# Open http://127.0.0.1:5000
```

## Usage
1. Drag a PDF/DOCX into the uploader (or click to select).
2. Optionally add “Additional Instructions” to focus the analysis.
3. Click “Analyze Document.”
4. View the ASCII diagram in the Response area (monospace code block).

'''
## API

### POST /api/analyze
Multipart form-data fields:
- file: PDF or DOCX (required)
- user_prompt: string (optional)
- model: string (optional; defaults to gemini-2.0-flash)

Response (JSON):
```json
{
  "model": "gemini-2.0-flash",
  "filename": "your-file.pdf",
  "response": "ASCII diagram string here"
}
```

## Backend Details
- Flask handles upload and calls Gemini.
- Text extraction:
  - PDF: pdfminer.six
  - DOCX: python-docx
- Input normalization:
  - Converts smart quotes/dashes to ASCII
  - Strips non-printable control chars
  - Prevents header/payload encoding errors
- Prompt composition:
  - Fixed system instruction enforcing format
  - Optional user_prompt
  - Extracted document text prefixed with `file text:\n...`

## Models
- gemini-2.0-flash: fast and cost-efficient.
- gemini-2.0-pro: higher quality analysis.

## Troubleshooting
- 500 on /api/analyze:
  - Ensure GEMINI_API_KEY is set and valid.
  - Check requirements installed.
- UnicodeEncodeError:
  - Fixed by input normalization; use the latest app.py.
- Empty diagram:
  - Verify the document contains extractable text (scanned PDFs may need OCR first).

## Security Notes
- Keep GEMINI_API_KEY server-side only.
- Limit file size via MAX_CONTENT_LENGTH (default 25MB).
- Validate file types (PDF/DOCX) before processing.

## License
MIT

## Roadmap
- Streaming responses (SSE).
- Multi-file analysis and comparison.
- Download diagram as .txt.

- Optional native Gemini File API integration.
