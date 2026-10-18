"""Command-line interface:  python generate_resume.py [resume.yaml] [options]"""
import argparse
import re
import sys
import time
from pathlib import Path

from . import template as T
from .errors import ResumeError
from .fonts import load_fonts
from .layout import layout_resume
from .model import check_glyphs, check_markup, load_resume
from .render import render_pdf, write_atomic


def default_filename(name: str) -> str:
    """'<firstName> <lastName>' -> '<firstName>_<lastName>_Resume.pdf' (the reference's pattern)."""
    stem = re.sub(r"[^\w.-]+", "_", name.strip()).strip("._") or "Resume"
    return f"{stem}_Resume.pdf"


def resolve_output(output, name) -> Path:
    if not output:
        return Path(default_filename(name))
    p = Path(output).expanduser()
    if p.is_dir() or str(output).endswith(("/", "\\")):
        return p / default_filename(name)
    return p if p.suffix.lower() == ".pdf" else p.with_name(p.name + ".pdf")


def generate(config, output=None, font_adjust=0.0, font="auto",
             strict=False, allow_multipage=False, check_only=False):
    """Programmatic entry point. Returns a dict describing the result."""
    started = time.perf_counter()
    resume, warnings = load_resume(config)
    fonts = load_fonts(font)
    check_markup(resume)
    check_glyphs(resume, fonts)
    result = layout_resume(resume, fonts, font_adjust, strict, allow_multipage)
    out = resolve_output(output, resume.name)
    if not check_only:
        write_atomic(render_pdf(result, fonts, resume), out)
    return {
        "output": None if check_only else out,
        "pages": len(result.pages),
        "font": fonts.family,
        "body_size": result.sizes["body"],
        "extra_scale": result.extra_scale,
        "leading_scale": result.leading_scale,
        "auto_shrink": result.auto_shrink,
        "warnings": warnings + result.warnings,
        "ms": (time.perf_counter() - started) * 1000,
    }


def _font_adjust(value: str) -> float:
    try:
        number = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"expected a number such as +1, 0, -1 or -0.5; got {value!r}")
    if not (T.FONT_ADJUST_MIN <= number <= T.FONT_ADJUST_MAX):
        raise argparse.ArgumentTypeError(
            f"{number:+g} is out of range ({T.FONT_ADJUST_MIN:+g} to {T.FONT_ADJUST_MAX:+g})")
    return number


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="generate_resume",
        description="Render resume.yaml into a PDF using the fixed reference layout.")
    ap.add_argument("config", nargs="?", default="resume.yaml",
                    help="resume content file (default: resume.yaml)")
    ap.add_argument("-o", "--output", metavar="FILE",
                    help="output PDF path or folder (default: <Name>_-_Resume.pdf)")
    ap.add_argument("-f", "--font-adjust", type=_font_adjust, default=0.0, metavar="PT",
                    help=f"add PT points to every font size, e.g. +1, 0, -1 "
                         f"(range {T.FONT_ADJUST_MIN:+g}..{T.FONT_ADJUST_MAX:+g}; "
                         "write negatives as --font-adjust=-1 or -f -1)")
    ap.add_argument("--font", choices=("auto", "arial", "liberation"), default="auto",
                    help="font family (default: auto = Arial if installed, else bundled "
                         "Liberation Sans, which has identical metrics)")
    ap.add_argument("--strict", action="store_true",
                    help="never auto-shrink text to fit; fail instead")
    ap.add_argument("--allow-multipage", action="store_true",
                    help="if content cannot fit one page, continue onto more pages "
                         "instead of failing")
    ap.add_argument("--check", action="store_true",
                    help="validate and lay out only; do not write a PDF")
    ap.add_argument("-q", "--quiet", action="store_true", help="print errors only")
    args = ap.parse_args(argv)

    try:
        info = generate(args.config, args.output, args.font_adjust, args.font,
                        args.strict, args.allow_multipage, args.check)
    except ResumeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code

    for w in info["warnings"]:
        print(f"warning: {w}", file=sys.stderr)
    if not args.quiet:
        what = "Layout OK" if args.check else f"Wrote {info['output']}"
        print(f"{what}: {info['pages']} page(s), {info['font']} "
              f"{info['body_size']:g} pt body, {info['ms']:.0f} ms")
        notes = []
        if info["extra_scale"] < 1:
            notes.append(f"section/entry spacing at {info['extra_scale']:.0%}")
        if info["leading_scale"] < 1:
            notes.append(f"line spacing at {info['leading_scale']:.0%}")
        if info["auto_shrink"]:
            notes.append(f"text auto-shrunk by {-info['auto_shrink']:g} pt")
        if notes:
            print("  fitted to page: " + ", ".join(notes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
