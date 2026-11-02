"""Text utilities, document extraction and small HTML render helpers."""

import html
import re
from io import BytesIO


class ExtractionError(Exception):
    """Raised when an uploaded document cannot be extracted safely."""


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text or "", flags=re.UNICODE))


def compression_percent(original_words: int, output_words: int) -> float:
    if not original_words:
        return 0.0
    return round(max(0.0, (1 - output_words / original_words) * 100), 1)


def text_stats(text: str):
    text = text or ""
    sentences = len(re.findall(r"[^.!?]+[.!?]+|[^.!?]+$", text.strip())) if text.strip() else 0
    return {"words": count_words(text), "chars": len(text), "sentences": sentences}


def chunk_text(text: str, max_words: int = 600):
    """Split text into word-bounded chunks, preferring paragraph/sentence boundaries."""
    text = (text or "").strip()
    if not text:
        return [""]
    max_words = max(1, int(max_words))
    words = text.split()
    if len(words) <= max_words:
        return [text]
    chunks, current = [], []
    for paragraph in re.split(r"\n\s*\n", text):
        pwords = paragraph.split()
        if not pwords:
            continue
        while pwords:
            room = max_words - len(current)
            if room <= 0:
                chunks.append(" ".join(current)); current = []; room = max_words
            if len(pwords) <= room:
                current.extend(pwords); pwords = []
            else:
                # Prefer a sentence boundary near the target size.
                candidate = pwords[:room]
                boundary = max((i + 1 for i, w in enumerate(candidate) if re.search(r"[.!?][\"')\]]?$", w)), default=0)
                take = boundary if boundary >= max(1, room // 2) else room
                current.extend(pwords[:take]); pwords = pwords[take:]
                chunks.append(" ".join(current)); current = []
    if current:
        chunks.append(" ".join(current))
    return chunks or [text]


def extract_text_from_upload(filename: str, data: bytes):
    name = (filename or "").lower()
    try:
        if name.endswith(".txt"):
            text = data.decode("utf-8-sig", errors="replace")
            fmt, meta = "TXT", {}
        elif name.endswith(".pdf"):
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    raise ExtractionError("This PDF is password-protected. Upload an unlocked PDF.")
            pages = [(p.extract_text() or "").strip() for p in reader.pages]
            text = "\n\n".join(p for p in pages if p)
            fmt, meta = "PDF", {"pages": len(reader.pages)}
            if not text.strip():
                raise ExtractionError("No selectable text was found in this PDF. It may be scanned; OCR is not configured.")
        elif name.endswith(".docx"):
            from docx import Document
            doc = Document(BytesIO(data))
            parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    parts.append(" | ".join(cell.text.strip() for cell in row.cells))
            text = "\n\n".join(parts)
            fmt, meta = "DOCX", {}
        else:
            raise ExtractionError("Unsupported file type. Upload a PDF, DOCX or TXT file.")
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError(f"Could not read {filename}: {type(exc).__name__}: {exc}") from exc
    if not text.strip():
        raise ExtractionError("The uploaded file contains no extractable text.")
    meta.update({"format": fmt, "words": count_words(text)})
    return text, meta


def esc(value):
    return html.escape(str(value), quote=True)


def pill_html(label, tone="neutral"):
    colors = {"ok": ("#d1fae5", "#065f46"), "bad": ("#fee2e2", "#991b1b"),
              "warn": ("#fef3c7", "#92400e"), "neutral": ("#e2e8f0", "#334155")}
    bg, fg = colors.get(tone, colors["neutral"])
    return f"<span style='display:inline-block;padding:4px 10px;border-radius:99px;background:{bg};color:{fg};font-size:12px;font-weight:700'>{esc(label)}</span>"


def callout_html(kind, title, message=None):
    if message is None:
        message, title = title, ""
    colors = {"success": ("#dcfce7", "#166534"), "ok": ("#dcfce7", "#166534"),
              "info": ("#dbeafe", "#1e40af"), "warn": ("#fef3c7", "#92400e"),
              "warning": ("#fef3c7", "#92400e"), "error": ("#fee2e2", "#991b1b")}
    bg, fg = colors.get(kind, colors["info"])
    heading = f"<div style='font-weight:750;margin-bottom:3px'>{esc(title)}</div>" if title else ""
    return f"<div style='padding:12px 14px;border-radius:12px;background:{bg};color:{fg};margin:8px 0'>{heading}<div style='font-size:13px;line-height:1.5'>{esc(message)}</div></div>"


def chips_html(stats):
    labels = [("Words", stats.get("words", 0)), ("Characters", stats.get("chars", 0)), ("Sentences", stats.get("sentences", 0))]
    return "<div style='display:flex;flex-wrap:wrap;gap:7px;margin:8px 0'>" + "".join(
        f"<span style='padding:5px 9px;border-radius:20px;background:rgba(127,127,127,.13);font-size:12px'>{k}: <b>{v:,}</b></span>" for k, v in labels) + "</div>"


def table_html(headers, rows):
    th = "".join(f"<th style='text-align:left;padding:9px;border-bottom:1px solid #94a3b8'>{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td style='padding:9px;border-bottom:1px solid rgba(148,163,184,.25)'>{esc(c)}</td>" for c in row) + "</tr>" for row in rows)
    return f"<div style='overflow-x:auto'><table style='width:100%;border-collapse:collapse;font-size:12px'><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>"


def empty_state_html(title, message):
    return f"<div style='min-height:180px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:24px;border:1px dashed rgba(148,163,184,.4);border-radius:15px'><div style='font-weight:750;font-size:17px'>{esc(title)}</div><div style='opacity:.7;font-size:13px;margin-top:6px'>{esc(message)}</div></div>"


def copy_button_html(text, dark=True):
    """Generate a safe HTML copy button for Streamlit."""
    import json
    import html

    payload = json.dumps(str(text)).replace(
        "<", "\u003c"
    ).replace(
        ">", "\u003e"
    ).replace(
        "&", "\u0026"
    )

    text_color = "#edf2ff" if dark else "#1e293b"
    onclick = (
        "navigator.clipboard.writeText("
        + payload
        + ").then(() => { this.innerText = 'Copied!'; })"
        + ".catch(() => { this.innerText = 'Copy unavailable'; })"
    )

    return f"""
    <button
        type="button"
        onclick="{html.escape(onclick, quote=True)}"
        style="
            width:100%;
            height:38px;
            border:1px solid #8b7cff;
            border-radius:10px;
            background:transparent;
            color:{text_color};
            font-weight:700;
            cursor:pointer;
        ">
        Copy output
    </button>
    """


def is_backend_error(output):
    """Return True when the AI backend response indicates a failure."""

    if not isinstance(output, str):
        return True

    s = output.strip()

    # Empty or invalid response
    if not s:
        return True

    lower = s.lower()

    error_prefixes = (
        "❌",
        "⚠️",
        "error:",
        "http error:",
        "api error:",
        "groq api error:",
        "no summary was returned",
        "no summary was generated",
        "no output was returned",
    )

    return lower.startswith(error_prefixes)


def clean_backend_message(output):
    """Remove leading error icons from backend messages."""
    return re.sub(r"^(?:❌|⚠️)\s*", "", str(output or "")).strip()


