"""
Font resolution.

The reference uses Arial. Arial cannot be redistributed, so the project
bundles Liberation Sans (SIL Open Font License), which was designed to be
*metrically identical* to Arial: every glyph has the same advance width.
Because line wrapping depends only on advance widths, the layout (line
breaks, positions, page fit) is identical whichever of the two is used;
only subtle glyph shapes differ.

  --font auto        use Arial if all four styles are installed, else Liberation
  --font arial       require an installed Arial (error if not found)
  --font liberation  always use the bundled Liberation Sans (fully portable)
"""
from dataclasses import dataclass, field
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont, TTFError

from .errors import FontError

FACES = ("regular", "bold", "italic", "bolditalic")

BUNDLED_DIR = Path(__file__).resolve().parent.parent / "fonts"
LIBERATION_FILES = {
    "regular": "LiberationSans-Regular.ttf",
    "bold": "LiberationSans-Bold.ttf",
    "italic": "LiberationSans-Italic.ttf",
    "bolditalic": "LiberationSans-BoldItalic.ttf",
}

# Where Arial lives on common systems: (regular, bold, italic, bolditalic)
_ARIAL_LOCATIONS = [
    ("/System/Library/Fonts/Supplemental",        # macOS
     ("Arial.ttf", "Arial Bold.ttf", "Arial Italic.ttf", "Arial Bold Italic.ttf")),
    ("/Library/Fonts",                            # macOS (older / user-installed)
     ("Arial.ttf", "Arial Bold.ttf", "Arial Italic.ttf", "Arial Bold Italic.ttf")),
    ("C:/Windows/Fonts",                          # Windows
     ("arial.ttf", "arialbd.ttf", "ariali.ttf", "arialbi.ttf")),
    ("/usr/share/fonts/truetype/msttcorefonts",   # Linux ttf-mscorefonts
     ("Arial.ttf", "Arial_Bold.ttf", "Arial_Italic.ttf", "Arial_Bold_Italic.ttf")),
]


@dataclass
class FontSet:
    family: str
    names: dict                       # face -> registered reportlab font name
    fonts: dict                       # face -> TTFont
    ascent: float                     # fraction of em (regular face)
    descent: float                    # positive fraction of em
    _glyphs: frozenset = field(default=frozenset(), repr=False)

    def width(self, text: str, face: str, size: float) -> float:
        return pdfmetrics.stringWidth(text, self.names[face], size)

    def missing_glyphs(self, text: str) -> list:
        """Characters that are not present in every face of this family."""
        seen, out = set(), []
        for ch in text:
            if ch not in seen and ord(ch) not in self._glyphs:
                seen.add(ch)
                out.append(ch)
        return out


def _find_arial():
    for folder, files in _ARIAL_LOCATIONS:
        paths = [Path(folder) / f for f in files]
        if all(p.is_file() for p in paths):
            return dict(zip(FACES, paths))
    return None


def _register(family: str, paths: dict) -> FontSet:
    names, fonts = {}, {}
    for face in FACES:
        name = f"Resume-{family}-{face}"
        if name not in pdfmetrics.getRegisteredFontNames():
            try:
                pdfmetrics.registerFont(TTFont(name, str(paths[face])))
            except (TTFError, OSError) as exc:
                raise FontError(f"Could not load font file {paths[face]}: {exc}") from exc
        names[face] = name
        fonts[face] = pdfmetrics.getFont(name)

    # A character is usable only if every face has it (safe for any style).
    glyph_sets = [set(fonts[f].face.charToGlyph.keys()) for f in FACES]
    common = frozenset(set.intersection(*glyph_sets))
    reg = fonts["regular"].face
    return FontSet(
        family=family, names=names, fonts=fonts,
        ascent=reg.ascent / 1000.0, descent=abs(reg.descent) / 1000.0,
        _glyphs=common,
    )


def load_fonts(choice: str = "auto") -> FontSet:
    choice = (choice or "auto").lower()
    if choice not in ("auto", "arial", "liberation"):
        raise FontError(f"Unknown font choice {choice!r}; use auto, arial or liberation.")

    if choice in ("auto", "arial"):
        arial = _find_arial()
        if arial:
            try:
                return _register("Arial", arial)
            except FontError:
                if choice == "arial":
                    raise
        elif choice == "arial":
            raise FontError(
                "Arial was requested but not found in the standard font folders. "
                "Use --font liberation (metrically identical) or install Arial."
            )

    paths = {face: BUNDLED_DIR / fname for face, fname in LIBERATION_FILES.items()}
    missing = [str(p) for p in paths.values() if not p.is_file()]
    if missing:
        raise FontError("Bundled font files are missing: " + ", ".join(missing))
    return _register("LiberationSans", paths)
