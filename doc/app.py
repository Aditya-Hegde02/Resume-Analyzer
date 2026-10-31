from __future__ import annotations

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from resume_ai.analyzer import analyze_resume
from resume_ai.pdf_utils import extract_pdf_text


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"


def _json_response(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    data = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _parse_content_disposition(value: str) -> dict[str, str]:
    parts = [part.strip() for part in value.split(";")]
    parsed: dict[str, str] = {}
    for part in parts[1:]:
        if "=" not in part:
            continue
        key, raw = part.split("=", 1)
        parsed[key.strip().lower()] = raw.strip().strip('"')
    return parsed


def _parse_multipart(body: bytes, content_type: str) -> tuple[dict[str, str], dict[str, dict]]:
    marker = "boundary="
    if marker not in content_type:
        raise ValueError("Missing multipart boundary.")

    boundary = content_type.split(marker, 1)[1].split(";", 1)[0].strip().strip('"')
    delimiter = ("--" + boundary).encode("utf-8")
    fields: dict[str, str] = {}
    files: dict[str, dict] = {}

    for raw_part in body.split(delimiter):
        part = raw_part.strip()
        if not part or part == b"--":
            continue
        if part.endswith(b"--"):
            part = part[:-2].strip()
        if b"\r\n\r\n" not in part:
            continue

        header_blob, content = part.split(b"\r\n\r\n", 1)
        headers: dict[str, str] = {}
        for line in header_blob.decode("utf-8", errors="replace").split("\r\n"):
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            headers[key.lower()] = value.strip()

        disposition = _parse_content_disposition(headers.get("content-disposition", ""))
        name = disposition.get("name")
        if not name:
            continue

        content = content.rstrip(b"\r\n")
        filename = disposition.get("filename", "")
        if filename:
            files[name] = {
                "filename": filename,
                "content_type": headers.get("content-type", "application/octet-stream"),
                "content": content,
            }
        else:
            fields[name] = content.decode("utf-8", errors="replace").strip()

    return fields, files


class ResumeAnalyzerHandler(BaseHTTPRequestHandler):
    server_version = "LocalResumeAnalyzer/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        requested = unquote(parsed.path)
        if requested == "/":
            requested = "/index.html"

        target = (STATIC_DIR / requested.lstrip("/")).resolve()
        if not str(target).startswith(str(STATIC_DIR.resolve())) or not target.is_file():
            self.send_error(404, "Not found")
            return

        content = target.read_bytes()
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/analyze":
            _json_response(self, {"error": "Unknown endpoint."}, status=404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            content_type = self.headers.get("Content-Type", "")
            body = self.rfile.read(length)
            fields, files = _parse_multipart(body, content_type)

            resume_text = fields.get("resume_text", "")
            uploaded = files.get("resume_pdf")
            pdf_status = {
                "source": "text",
                "filename": "",
                "extractor": "manual input",
                "warnings": [],
            }

            if uploaded and uploaded["content"]:
                resume_text, pdf_status = extract_pdf_text(uploaded["content"], uploaded["filename"])

            if len(resume_text.strip()) < 80:
                _json_response(
                    self,
                    {
                        "error": "Could not extract enough resume text. Try another PDF or paste the resume text.",
                        "pdf_status": pdf_status,
                    },
                    status=422,
                )
                return

            result = analyze_resume(
                resume_text=resume_text,
                job_description=fields.get("job_description", ""),
                target_role=fields.get("target_role", ""),
                pdf_status=pdf_status,
            )
            _json_response(self, result)
        except Exception as exc:  # Defensive so local server keeps running.
            _json_response(self, {"error": str(exc)}, status=500)

    def log_message(self, format: str, *args) -> None:
        if os.environ.get("RESUME_ANALYZER_VERBOSE"):
            super().log_message(format, *args)


def main() -> None:
    host = os.environ.get("RESUME_ANALYZER_HOST", "127.0.0.1")
    port = int(os.environ.get("RESUME_ANALYZER_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), ResumeAnalyzerHandler)
    print(f"Local Resume Analyzer running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
