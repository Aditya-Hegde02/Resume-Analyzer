from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import zlib
from pathlib import Path


def _clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\x00", " ")
    text = "".join(char for char in text if char in "\n\t" or char.isprintable())
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _is_usable_text(text: str) -> bool:
    cleaned = _clean_text(text)
    if len(cleaned) < 80:
        return False
    readable = sum(char.isprintable() for char in cleaned) / max(len(cleaned), 1)
    if readable < 0.97 or cleaned.count("\ufffd") > 2:
        return False
    unusual = re.findall(r"[^\w\s.,;:!?%&@#$()+\-/'\"…–—•|]", cleaned)
    if len(unusual) / len(cleaned) > 0.06:
        return False
    words = re.findall(r"[A-Za-z]+", cleaned)
    single_letters = re.findall(r"\b[A-Za-z]\b", cleaned)
    if len(words) >= 50 and len(single_letters) >= 10 and len(single_letters) / len(words) > 0.14:
        return False
    return len(re.findall(r"[A-Za-z0-9]", cleaned)) / len(cleaned) > 0.35


def _decode_pdf_literal(value: str) -> str:
    value = value.replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\")
    value = value.replace(r"\n", "\n").replace(r"\r", "\n").replace(r"\t", "\t")
    value = re.sub(r"\\([0-7]{1,3})", lambda m: chr(int(m.group(1), 8)), value)
    return value


def _extract_from_content(content: bytes) -> str:
    decoded = content.decode("latin-1", errors="ignore")
    chunks: list[str] = []

    for match in re.finditer(r"\((?:\\.|[^\\)])*\)\s*Tj", decoded, flags=re.S):
        raw = match.group(0).rsplit(")", 1)[0][1:]
        chunks.append(_decode_pdf_literal(raw))

    for array in re.finditer(r"\[(.*?)\]\s*TJ", decoded, flags=re.S):
        inside = array.group(1)
        for raw in re.findall(r"\((?:\\.|[^\\)])*\)", inside):
            chunks.append(_decode_pdf_literal(raw[1:-1]))
        for raw_hex in re.findall(r"<([0-9A-Fa-f\s]+)>", inside):
            try:
                data = bytes.fromhex(re.sub(r"\s+", "", raw_hex))
                chunks.append(data.decode("utf-16-be", errors="ignore") or data.decode("latin-1", errors="ignore"))
            except ValueError:
                continue

    text = " ".join(chunk.strip() for chunk in chunks if chunk.strip())
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    return _clean_text(text)


def _extract_with_pypdf(data: bytes) -> tuple[str, str] | None:
    try:
        from pypdf import PdfReader  # type: ignore

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(data)
            tmp_path = Path(tmp.name)
        try:
            reader = PdfReader(str(tmp_path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            if _is_usable_text(text):
                return _clean_text(text), "pypdf"
        finally:
            tmp_path.unlink(missing_ok=True)
    except Exception:
        return None
    return None


def _extract_with_pdftotext(data: bytes) -> tuple[str, str] | None:
    exe = shutil.which("pdftotext")
    if not exe:
        return None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(data)
            input_path = Path(tmp.name)
        output_path = input_path.with_suffix(".txt")
        try:
            subprocess.run([exe, "-layout", str(input_path), str(output_path)], check=False, capture_output=True, timeout=10)
            if output_path.exists():
                text = output_path.read_text(encoding="utf-8", errors="replace")
                if _is_usable_text(text):
                    return _clean_text(text), "pdftotext"
        finally:
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)
    except Exception:
        return None
    return None


def _extract_with_builtin_parser(data: bytes) -> tuple[str, str]:
    texts: list[str] = []
    for stream in re.finditer(rb"(<<.*?>>)\s*stream\r?\n(.*?)\r?\nendstream", data, flags=re.S):
        header, content = stream.group(1), stream.group(2)
        if b"FlateDecode" in header:
            try:
                content = zlib.decompress(content)
            except zlib.error:
                continue
        elif b"/Filter" in header:
            # Do not interpret streams encoded with filters this parser cannot decode.
            continue
        extracted = _extract_from_content(content)
        if extracted:
            texts.append(extracted)

    if not texts:
        texts.append(_extract_from_content(data))

    text = _clean_text("\n".join(texts))
    return (text if _is_usable_text(text) else ""), "built-in parser"


def extract_pdf_text(data: bytes, filename: str) -> tuple[str, dict]:
    status = {
        "source": "pdf",
        "filename": filename,
        "extractor": "",
        "warnings": [],
    }

    for extractor in (_extract_with_pypdf, _extract_with_pdftotext):
        result = extractor(data)
        if result:
            text, name = result
            status["extractor"] = name
            return text, status

    text, name = _extract_with_builtin_parser(data)
    status["extractor"] = name
    if not text:
        status["warnings"].append(
            "Readable text could not be extracted. This PDF may be scanned or use an unsupported font encoding. Paste the resume text into the fallback field."
        )
    else:
        status["warnings"].append("Text was extracted with the basic parser; review it for layout or spacing issues.")
    return text, status
