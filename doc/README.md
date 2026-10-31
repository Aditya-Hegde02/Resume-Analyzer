# Resume Studio

A local-first resume analysis dashboard. Upload a PDF or paste resume text, add a target role and job description, and review ATS-style signals, keyword coverage, writing quality, and suggested improvements.

Resume Studio runs on your machine. Resume files and analysis text are processed by the local Python server and are not sent to a hosted analysis service.

## Features

- Resume PDF upload with an in-browser PDF preview
- Paste-in text option for scanned PDFs or PDFs with unsupported text encoding
- ATS-style overall score and score profile
- Keyword match and missing-keyword analysis against a job description
- Contact and resume-section checks
- Technical skills, soft skills, and action verb detection
- Formatting, role fit, readability, and achievement signals
- Recruiter-style overview, content audit, and prioritized recommendations
- Deep analysis with risk flags, section depth, and interview preparation topics
- Responsive dashboard with score colors and visual analytics
- Local keyword-vector similarity with the included TF-IDF model

## Requirements

- Python 3.10 or later
- A modern browser

The app has no required third-party Python packages. PDF extraction uses available local tools in this order: `pypdf`, `pdftotext`, then a limited built-in parser. Scanned PDFs generally need OCR; paste their text into the fallback field when extraction is unavailable or garbled.

## Run locally

Clone the repository and move into its directory:

```bash
git clone <repository-url>
cd <repository-directory>
```

Start the server:

```bash
python app.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. Stop the server with `Ctrl+C`.

On some Windows installations, use `py app.py` instead of `python app.py`.

## Use the dashboard

1. Choose a resume PDF, or paste resume text in the fallback field.
2. Enter a target role and, optionally, paste the job description.
3. Select **Analyze locally**.
4. Explore the Overview, Skills, ATS details, Deep analysis, Recruiter view, Content audit, Suggestions, and PDF tabs.

The PDF tab previews the selected original document. Extracted text is available below the preview when it can be decoded reliably.

## Configuration

The server defaults to `127.0.0.1:8000`. Override the bind address or port with environment variables:

**PowerShell**

```powershell
$env:RESUME_ANALYZER_HOST = "127.0.0.1"
$env:RESUME_ANALYZER_PORT = "8000"
python app.py
```

**macOS / Linux**

```bash
RESUME_ANALYZER_HOST=127.0.0.1 RESUME_ANALYZER_PORT=8000 python app.py
```

The included model is stored at `models/resume_model/model.json`. To regenerate it:

```bash
python scripts/train_local_model.py
```

To point to a different local model directory, set `RESUME_MODEL_PATH` before starting the server. A local SentenceTransformer model can be used if the `sentence-transformers` package is installed; otherwise the app falls back to its built-in local scorer.

## Project layout

```text
.
├── app.py                    # Local HTTP server and /analyze endpoint
├── resume_ai/
│   ├── analyzer.py            # Resume scoring and insight generation
│   ├── model_adapter.py       # Local similarity model adapter
│   └── pdf_utils.py           # PDF text extraction and quality checks
├── models/resume_model/       # Included local TF-IDF model
├── scripts/train_local_model.py
└── static/
    ├── index.html             # Dashboard structure
    ├── styles.css             # Responsive dashboard styling
    └── app.js                 # Tabs, PDF preview, charts, and form handling
```

## Privacy and limitations

- The default server binds to `127.0.0.1`, keeping it accessible only from the local machine.
- Resume analysis is heuristic and intended as guidance; it is not a hiring decision or a guarantee of ATS performance.
- PDF extraction quality depends on the document. Image-only/scanned PDFs require OCR or pasted text.
- The default similarity model is a compact local TF-IDF model, not a hosted generative AI service.
