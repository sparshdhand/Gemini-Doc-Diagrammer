# Gemini-Doc-Diagrammer
# Document Analyzer – AI-Powered ASCII Diagrams
Transform PDF/DOCX documents into clear ASCII diagrams using Google AI
Studio (Gemini). Upload a file, optionally add extra instructions, and
get a formatted code block that visualizes classes, relationships, and
changes---bounded by 60-underscore lines.\
**Features**

-   Drag-and-drop upload for PDF and DOCX

-   Server-side text extraction (pdfminer.six, python-docx)

-   Gemini backend via google-genai SDK

-   Enforced output format (code block, 60-character borders, 60-char
    line cap)

-   Optional user instructions appended to system prompt

-   Simple Flask API and minimal frontend\
    **Quick Start**\
    Prerequisites

```{=html}
<!-- -->
```
-   Python 3.10+ (tested on 3.11--3.14)

-   A Google AI Studio API key (Gemini)\
    **Project Structure**\
    `project/  `\
    ├─` app.py  `\
    ├─` requirements.txt  `\
    └─` static/  `\
    `   `└─` index.html  `\
    **Install**\
    `# From project root  `\
    `python -m venv .venv  `\
    `source .venv/bin/activate  # Windows: .venv``\``Scripts``\``activate  `\
    `pip install -r requirements.txt  `\
    **Configure**\
    `# Set your Gemini API key  `\
    `export GEMINI_API_KEY="YOUR_KEY"      # macOS/Linux  `\
    `# PowerShell:  `\
    `# setx GEMINI_API_KEY "YOUR_KEY" && restart terminal  `\
    **Run**\
    `python app.py  `\
    `# Open http://127.0.0.1:5000  `\
    **Usage**

1.  Drag a PDF/DOCX into the uploader (or click to select).

2.  Optionally add "Additional Instructions" to focus the analysis.

3.  Click "Analyze Document."

4.  View the ASCII diagram in the Response area (monospace code block).\
    **API**\
    POST /api/analyze\
    Multipart form-data:

-   file: PDF or DOCX (required)

-   user_prompt: string (optional)

-   model: string (optional; defaults to gemini-2.0-flash)\
    Response (JSON):

```{=html}
<!-- -->
```
-   model: chosen model

-   filename: original filename

-   response: ASCII diagram string (in code-block format)\
    **Backend Details**

```{=html}
<!-- -->
```
-   Flask handles upload and calls Gemini.

-   Text extraction:

    -   PDF: pdfminer.six

    -   DOCX: python-docx

```{=html}
<!-- -->
```
-   Input normalization:

    -   Converts smart quotes/dashes to ASCII

    -   Strips non-printable control chars

    -   Prevents header/payload encoding errors

```{=html}
<!-- -->
```
-   Prompt composition:

    -   Fixed system instruction enforcing format

    -   Optional user_prompt

    -   Extracted document text prefixed with "file text:\\n..."\
        **Models**

```{=html}
<!-- -->
```
-   gemini-2.0-flash: fast and cost-efficient

-   gemini-2.0-pro: higher quality analysis\
    **Troubleshooting**

```{=html}
<!-- -->
```
-   500 on /api/analyze:

    -   Ensure GEMINI_API_KEY is set and valid.

    -   Check requirements installed.

```{=html}
<!-- -->
```
-   UnicodeEncodeError:

    -   Fixed by input normalization; update to the latest app.py.

```{=html}
<!-- -->
```
-   Empty diagram:

    -   Verify the document contains extractable text (scanned PDFs may
        need OCR first).\
        **Security Notes**

```{=html}
<!-- -->
```
-   Keep GEMINI_API_KEY server-side only.

-   Limit file size via MAX_CONTENT_LENGTH (default 25MB).

-   Validate file types (PDF/DOCX) before processing.\
    **License**\
    MIT\
    **Roadmap**

```{=html}
<!-- -->
```
-   Streaming responses (SSE)

-   Multi-file analysis and comparison

-   Download diagram as .txt

-   Optional native Gemini File API integration
