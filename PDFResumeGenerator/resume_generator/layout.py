"""
Layout engine: turns a validated Resume into positioned text runs.

Pipeline
  1. build_lines()  - map each YAML value into its fixed template slot and
                      word-wrap it, producing a flat list of Lines. Each Line
                      names the template gap that precedes it.
  2. place()        - convert gaps into baselines and paginate.
  3. layout_resume()- try the natural spacing, then the fit ladder from
                      template.py, until the content fits TARGET_PAGES.

Everything is pure arithmetic on font metrics: same input, same output.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from . import template as T
from .errors import LayoutError


# ------------------------------------------------------------ primitives
@dataclass(frozen=True)
class Style:
    face: str                       # regular | bold | italic | bolditalic
    size_role: str                  # key into template.SIZES
    color: tuple = T.BLACK
    url: Optional[str] = None


@dataclass
class Run:
    x: float
    text: str
    style: Style
    size: float          # drawn font size
    advance: float       # layout size used for glyph advances (see template)
    width: float


@dataclass
class Line:
    gap: str                        # key into template.GAPS
    runs: List[Run]
    size: float                     # tallest font size on the line
    rule: bool = False              # draw a section rule under this line
    bullet: bool = False            # draw a bullet dot before this line
    keep_with_next: bool = False


@dataclass
class Placed:
    line: Line
    baseline: float                 # y from top of page


@dataclass
class LayoutResult:
    pages: List[List[Placed]]
    sizes: dict
    scale: float
    extra_scale: float
    leading_scale: float
    auto_shrink: float
    warnings: List[str] = field(default_factory=list)


# ------------------------------------------------------------ wrapping
# Break opportunities: after a space, and after a hyphen between word
# characters ("proof-of-|concept"), which is how Word wraps.
_HYPHEN_BREAK = re.compile(r"(?<=\w-)(?=\w)")
_EPS = 0.01


@dataclass
class _Piece:
    text: str
    style: Style
    space_after: bool = False
    break_after: bool = False


class _Wrapper:
    def __init__(self, fonts, advances, warnings):
        self.fonts, self.advances, self.warnings = fonts, advances, warnings

    def w(self, text, style):
        return self.fonts.width(text, style.face, self.advances[style.size_role])

    def _pieces(self, segments):
        pieces = []
        for text, style in segments:
            for tok in re.findall(r" +|[^ ]+", text):
                if tok[0] == " ":
                    if pieces:
                        pieces[-1].space_after = pieces[-1].break_after = True
                    continue
                subs = _HYPHEN_BREAK.split(tok)
                for k, sub in enumerate(subs):
                    pieces.append(_Piece(sub, style, break_after=k < len(subs) - 1))
        return pieces

    def wrap(self, segments, width, context) -> List[List[Tuple[str, Style]]]:
        """Greedy fill identical to Word: a trailing space never counts."""
        # group pieces into unbreakable units
        units, cur = [], []
        for p in self._pieces(segments):
            cur.append(p)
            if p.break_after:
                units.append(cur)
                cur = []
        if cur:
            units.append(cur)

        lines, line, used, pending = [], [], 0.0, 0.0
        for unit in units:
            uw = sum(self.w(p.text, p.style) for p in unit)
            if line and used + pending + uw > width + _EPS:
                lines.append(line)
                line, used, pending = [], 0.0, 0.0
            if not line and uw > width + _EPS:
                # A single word wider than the line (e.g. a very long URL).
                self.warnings.append(f"{context}: '{''.join(p.text for p in unit)}' is "
                                     "wider than the line and was broken mid-word")
                for chunk in self._hard_split(unit, width):
                    lines.append(chunk)
                line, used, pending = [], 0.0, 0.0
                last = unit[-1]
                if lines and not last.space_after:
                    # keep the tail open so following text can join it
                    line = lines.pop()
                    used = sum(self.w(p.text, p.style) for p in line)
                continue
            line.extend(unit)
            used += pending + uw
            last = unit[-1]
            pending = self.w(" ", last.style) if last.space_after else 0.0
        if line:
            lines.append(line)
        return [self._to_segments(l) for l in lines]

    def _hard_split(self, unit, width):
        out, line, used = [], [], 0.0
        for p in unit:
            for ch in p.text:
                cw = self.w(ch, p.style)
                if line and used + cw > width + _EPS:
                    out.append(line)
                    line, used = [], 0.0
                line.append(_Piece(ch, p.style))
                used += cw
            if line and p.space_after:
                line[-1].space_after = True
        if line:
            out.append(line)
        return out

    @staticmethod
    def _to_segments(pieces):
        segs = []
        for i, p in enumerate(pieces):
            text = p.text + (" " if p.space_after and i < len(pieces) - 1 else "")
            if segs and segs[-1][1] == p.style:
                segs[-1] = (segs[-1][0] + text, p.style)
            else:
                segs.append((text, p.style))
        return segs


# ------------------------------------------------------------ line builder
NAME = Style("bold", "name", T.GRAY)
CONTACT = Style("regular", "contact")
SECTION = Style("bold", "section", T.GRAY)
HEADING = Style("bold", "heading", T.GRAY)
ROLE = Style("italic", "role")
BODY = Style("regular", "body")
SKILL_LABEL = Style("bold", "body")
_BOLDER = {"regular": "bold", "italic": "bolditalic", "bold": "bold", "bolditalic": "bolditalic"}
HEADLINE = Style("bold", "body")

def markup(text, style):
    """Split '**bold**' markup into (text, style) segments. Odd parts are bold."""
    bold = Style(_BOLDER[style.face], style.size_role, style.color, style.url)
    return [(part, bold if i % 2 else style)
            for i, part in enumerate(text.split("**")) if part]

class _Builder:
    def __init__(self, fonts, sizes, advances):
        self.fonts, self.sizes, self.advances = fonts, sizes, advances
        self.warnings = []
        self.wrapper = _Wrapper(fonts, advances, self.warnings)
        self.lines: List[Line] = []

    # -- helpers
    def _runs(self, segments, x):
        runs = []
        for text, style in segments:
            size = self.sizes[style.size_role]
            adv = self.advances[style.size_role]
            w = self.fonts.width(text, style.face, adv)
            runs.append(Run(x, text, style, size, adv, w))
            x += w
        return runs

    def _add(self, gap, runs, **kw):
        size = max(r.size for r in runs)
        self.lines.append(Line(gap, runs, size, **kw))

    def _width(self, segments):
        return sum(self.fonts.width(t, s.face, self.advances[s.size_role]) for t, s in segments)

    def _centered(self, gap, segments, context, **kw):
        w = self._width(segments)
        if w > T.CONTENT_WIDTH + _EPS:
            raise LayoutError(f"{context} is {w - T.CONTENT_WIDTH:.1f} pt too wide to fit "
                              "on one line. Shorten it or use a smaller --font-adjust.")
        self._add(gap, self._runs(segments, T.CONTENT_LEFT + (T.CONTENT_WIDTH - w) / 2), **kw)

    def _left_right(self, gap, left, right, context, **kw):
        lw = self._width(left)
        rw = self._width(right) if right else 0.0
        room = T.CONTENT_WIDTH - (rw + T.MIN_COLUMN_GAP if right else 0.0)
        if lw > room + _EPS:
            raise LayoutError(
                f"{context}: text is {lw - room:.1f} pt too long"
                + (" and would collide with the date on the right" if right else "")
                + ". Shorten it (this line cannot wrap).")
        runs = self._runs(left, T.CONTENT_LEFT)
        if right:
            runs += self._runs(right, T.CONTENT_RIGHT - rw)
        self._add(gap, runs, **kw)

    def _paragraph(self, first_gap, segments, x, context, bullet=False):
        wrapped = self.wrapper.wrap(segments, T.CONTENT_RIGHT - x, context)
        for i, segs in enumerate(wrapped):
            # keep a paragraph's lines together when paginating
            self._add(first_gap if i == 0 else "line", self._runs(segs, x),
                      bullet=bullet and i == 0, keep_with_next=i < len(wrapped) - 1)

    def _section(self, key, gap):
        self._add(gap, self._runs([(T.SECTION_TITLES[key], SECTION)], T.CONTENT_LEFT),
                  rule=True, keep_with_next=True)

    # -- template
    def build(self, r):
        self._centered("line", [(r.name, NAME)], "The name", keep_with_next=True)

        # Contact items share one centered line; if they cannot, they wrap at
        # the " | " separators onto further centered lines.
        items = [(c.text, Style("regular", "contact", T.LINK_BLUE, c.url) if c.url else CONTACT)
                 for c in r.contact]
        rows, row = [], []
        for item in items:
            trial = row + ([(T.CONTACT_SEPARATOR, CONTACT)] if row else []) + [item]
            if row and self._width(trial) > T.CONTENT_WIDTH + _EPS:
                rows.append(row)
                row = [item]
            else:
                row = trial
        rows.append(row)
        if len(rows) > 1:
            self.warnings.append(f"The contact line was too wide for one line and was "
                                 f"wrapped onto {len(rows)} lines.")
        for i, row in enumerate(rows):
            self._centered("name_to_contact" if i == 0 else "line", row,
                           f"Contact item '{row[0][0]}'", keep_with_next=True)

        for n, key in enumerate(T.SECTION_ORDER):
            self._section(key, "contact_to_section" if n == 0 else "block_to_section")
            getattr(self, f"_{key}")(r)
        return self.lines

    def _summary(self, r):                                              
        gap = "section_to_paragraph"
        if r.headline:
            self._paragraph(gap, [(r.headline, HEADLINE)], T.CONTENT_LEFT, "headline")
            self.lines[-1].keep_with_next = True   # never separate headline from summary
            gap = "headline_to_paragraph"
        self._paragraph("section_to_paragraph", markup(r.summary, BODY), T.CONTENT_LEFT, "summary")

    def _experience(self, r):
        for i, job in enumerate(r.experience):
            where = f"experience[{i}]"
            heading = job.company + (T.PLACE_SEPARATOR + job.location if job.location else "")
            self._left_right("section_to_entry" if i == 0 else "entry_to_entry",
                             [(heading, HEADING)], None, f"{where} company/location",
                             keep_with_next=True)
            dates = job.start + T.DATE_SEPARATOR + job.end
            self._left_right("heading_to_role", [(job.title, ROLE)], [(dates, ROLE)],
                             f"{where}.title", keep_with_next=True)
            for k, bullet in enumerate(job.bullets):
                self._paragraph("role_to_bullet" if k == 0 else "bullet_to_bullet",
                                markup(bullet, BODY), T.BULLET_TEXT_X,
                                f"{where}.bullets[{k}]", bullet=True)

    def _education(self, r):
        for i, s in enumerate(r.education):
            heading = s.school + (T.PLACE_SEPARATOR + s.location if s.location else "")
            self._left_right("section_to_entry" if i == 0 else "edu_to_edu",
                             [(heading, HEADING)], [(s.date, ROLE)],
                             f"education[{i}].school/location", keep_with_next=True)
            self._paragraph("school_to_degree", markup(s.degree, BODY), T.CONTENT_LEFT,
                            f"education[{i}].degree")

    def _skills(self, r):
        for i, s in enumerate(r.skills):
            self._paragraph("section_to_skills" if i == 0 else "skill_to_skill",
                            [(s.label + T.SKILL_LABEL_SUFFIX + " ", SKILL_LABEL)]
                            + markup(s.items, BODY),
                            T.CONTENT_LEFT, f"skills[{i}]")


# ------------------------------------------------------------ placement
def _advance(gap, scale, extra_scale, leading_scale):
    total = T.GAPS[gap]
    extra = total - T.LINE_PITCH
    return scale * (T.LINE_PITCH * leading_scale + extra * extra_scale)


def place(lines, fonts, scale, extra_scale, leading_scale, paginate):
    """Assign baselines. Returns (pages, overflow_pt).

    Without pagination everything goes on one page and overflow_pt says how
    far the lowest descender passes BOTTOM_LIMIT (<= 0 means it fits).
    With pagination, lines that do not fit move to a new page, taking any
    keep-with-next predecessors (headers, company/title lines) along.
    """
    pages, page, y = [], [], None
    i = 0
    while i < len(lines):
        line = lines[i]
        if y is None:
            baseline = T.TOP_EDGE + T.ASCENT * line.size
        else:
            baseline = y + _advance(line.gap, scale, extra_scale, leading_scale)
        bottom = baseline + T.DESCENT * line.size
        if paginate and page and bottom > T.BOTTOM_LIMIT:
            start = len(page)
            while start > 1 and page[start - 1].line.keep_with_next:
                start -= 1
            moved = len(page) - start
            if moved and start > 0:
                del page[start:]
                i -= moved
            pages.append(page)
            page, y = [], None
            continue
        page.append(Placed(line, baseline))
        y = baseline
        i += 1
    pages.append(page)
    last = pages[-1][-1]
    overflow = last.baseline + T.DESCENT * last.line.size - T.BOTTOM_LIMIT
    return pages, overflow


# ------------------------------------------------------------ driver
def sizes_for(delta):
    return {role: round(size + delta, 4) for role, size in T.SIZES.items()}


def advances_for(delta):
    return {role: round(size + delta, 4) for role, size in T.ADVANCE_SIZES.items()}


def layout_resume(resume, fonts, font_adjust=0.0, strict=False, allow_multipage=False):
    if not (T.FONT_ADJUST_MIN <= font_adjust <= T.FONT_ADJUST_MAX):
        raise LayoutError(f"--font-adjust {font_adjust:+g} is out of range "
                          f"({T.FONT_ADJUST_MIN:+g} to {T.FONT_ADJUST_MAX:+g} points).")

    cache = {}

    def build(delta):
        if delta not in cache:
            b = _Builder(fonts, sizes_for(delta), advances_for(delta))
            cache[delta] = (b.build(resume), b.warnings)
        return cache[delta]

    ladder = list(T.SPACING_LADDER) + ([] if strict else list(T.SHRINK_LADDER))
    last_overflow = None
    for extra_scale, leading_scale, shrink in ladder:
        delta = round(font_adjust + shrink, 4)
        lines, warns = build(delta)
        scale = sizes_for(delta)["body"] / T.BODY_REF
        pages, overflow = place(lines, fonts, scale, extra_scale, leading_scale, paginate=False)
        last_overflow = overflow
        if overflow <= 0:
            return LayoutResult(pages, sizes_for(delta), scale, extra_scale,
                                leading_scale, shrink, list(warns))

    if allow_multipage:
        lines, warns = build(font_adjust)
        scale = sizes_for(font_adjust)["body"] / T.BODY_REF
        pages, _ = place(lines, fonts, scale, 1.0, 1.0, paginate=True)
        warns = list(warns) + [
            f"Content does not fit on {T.TARGET_PAGES} page(s) even with tightened "
            f"spacing; produced {len(pages)} pages with the original spacing."]
        return LayoutResult(pages, sizes_for(font_adjust), scale, 1.0, 1.0, 0.0, warns)

    body_pitch = T.LINE_PITCH * sizes_for(font_adjust)["body"] / T.BODY_REF
    tried = "tightening spacing" + ("" if strict else " and shrinking text by 0.5 pt")
    raise LayoutError(
        f"Content overflows {T.TARGET_PAGES} page by {last_overflow:.1f} pt "
        f"(about {max(1, round(last_overflow / body_pitch + 0.49))} line(s)) even after "
        f"{tried}. Shorten some bullets, use a smaller --font-adjust, "
        "or pass --allow-multipage.")
