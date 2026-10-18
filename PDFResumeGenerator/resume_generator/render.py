"""Draw a LayoutResult onto PDF pages with ReportLab's canvas.

`invariant=1` removes timestamps and random document IDs, so identical input
produces byte-identical PDFs.
"""
import io
import os
import tempfile
from pathlib import Path

from reportlab.pdfgen import canvas

from . import template as T
from .errors import OutputError


def render_pdf(result, fonts, resume) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(T.PAGE_WIDTH, T.PAGE_HEIGHT),
                      invariant=1, pageCompression=1)
    c.setTitle(f"{resume.name} - Resume")
    c.setAuthor(resume.name)
    c.setSubject("Resume")
    c.setCreator("resume-pdf-generator")

    H = T.PAGE_HEIGHT
    for page in result.pages:
        for placed in page:
            line, base = placed.line, placed.baseline
            for run in line.runs:
                st = run.style
                c.setFillColorRGB(*st.color)
                text = c.beginText(run.x, H - base)
                text.setFont(fonts.names[st.face], run.size)
                text.setHorizScale(100.0 * run.advance / run.size)
                text.textOut(run.text)
                c.drawText(text)
                if st.url:
                    top = base + T.UNDERLINE_OFFSET * result.scale
                    c.rect(run.x, H - top - T.UNDERLINE_THICKNESS, run.width,
                           T.UNDERLINE_THICKNESS, stroke=0, fill=1)
                    c.linkURL(st.url, (run.x, H - base - T.DESCENT * run.size,
                                       run.x + run.width, H - base + T.ASCENT * run.size),
                              relative=0, thickness=0)
            if line.bullet:
                body = result.sizes["body"]
                c.setFillColorRGB(*T.BLACK)
                c.circle(T.BULLET_CENTER_X, H - (base - T.BULLET_RISE_EM * body),
                         T.BULLET_DIAMETER_EM * body / 2, stroke=0, fill=1)
            if line.rule:
                top = base + T.RULE_OFFSET * result.scale
                c.setFillColorRGB(*T.BLACK)
                c.rect(T.RULE_LEFT, H - top - T.RULE_THICKNESS, T.RULE_RIGHT - T.RULE_LEFT,
                       T.RULE_THICKNESS, stroke=0, fill=1)
        c.showPage()
    c.save()
    return buf.getvalue()


def write_atomic(data: bytes, out_path: Path) -> None:
    """Write via a temp file + rename, so a failure never leaves a half PDF."""
    out_path = Path(out_path)
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".resume-", suffix=".pdf", dir=out_path.parent)
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
            os.replace(tmp, out_path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
    except PermissionError as exc:
        raise OutputError(f"Cannot write {out_path}: permission denied. If the PDF is open "
                          "in a viewer, close it and try again.") from exc
    except OSError as exc:
        raise OutputError(f"Cannot write {out_path}: {exc}") from exc
