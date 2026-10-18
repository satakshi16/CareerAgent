"""
Fixed layout template, derived once from the author's original resume PDF
(not included in the repo) and hard-coded here.

Every number below was measured from the reference with pdfplumber
(character bounding boxes, font names/sizes, fill colors, baselines,
rectangles and link annotations). Units are PostScript points (1/72 in),
with y measured DOWN from the top edge of the page.

This is the ONLY file that encodes visual design. Resume content lives in
the YAML file; layout logic lives in layout.py. Nothing here should need to
change when the resume content changes.
"""

# --------------------------------------------------------------------------
# Page geometry  (reference: 612 x 792 pt = US Letter, 1 page)
# --------------------------------------------------------------------------
PAGE_WIDTH = 612.0
PAGE_HEIGHT = 792.0
TARGET_PAGES = 1                      # the reference resume is one page

MARGIN_LEFT = 43.92                   # every left-aligned line starts at x=43.92
MARGIN_RIGHT = 43.92                  # right-aligned dates end at x=568.06
CONTENT_LEFT = MARGIN_LEFT
CONTENT_RIGHT = PAGE_WIDTH - MARGIN_RIGHT   # 568.08
CONTENT_WIDTH = CONTENT_RIGHT - CONTENT_LEFT

# The name's baseline sits at 53.28; Arial's ascent is 0.905 em, so the top
# of the first line box is 53.28 - 0.905 * 16.08 = 38.73.
TOP_EDGE = 38.73
# Lowest point any glyph descender may reach. The reference's last line
# bottoms out at 750.7, leaving ~5 pt of slack above a 0.5 in bottom margin.
BOTTOM_LIMIT = PAGE_HEIGHT - 36.0

# --------------------------------------------------------------------------
# Typography  (reference: Arial family, WinAnsi, no kerning)
# --------------------------------------------------------------------------
SIZES = {
    "name": 16.08,      # "JORDAN LEE"               Arial Bold
    "contact": 10.56,   # contact line               Arial
    "section": 10.56,   # "SUMMARY", "EXPERIENCE"... Arial Bold
    "heading": 10.08,   # "Acme Analytics – Austin"  Arial Bold  (subsection)
    "role": 10.08,      # "Data Science Manager"     Arial Italic (subsection)
    "body": 10.08,      # paragraphs, bullets, skills
}
BODY_REF = SIZES["body"]

# Word lays glyphs out on a slightly tighter grid than the drawn size. Measured
# from ~3,400 character advances in the reference, the advance widths equal
# Arial's metrics at these sizes (e.g. body glyphs are drawn at 10.08 pt but
# advance as if 10.0 pt: 'W' = 9.442 pt instead of 9.514). Reproducing this is
# what makes line breaks land on exactly the same words as the reference.
# The renderer applies it as a PDF horizontal text scale (<= 0.8%).
ADVANCE_SIZES = {
    "name": 16.0,
    "contact": 10.5,
    "section": 10.5,
    "heading": 10.0,
    "role": 10.0,
    "body": 10.0,
}

# Arial vertical metrics (hhea), as used by Word for line boxes.
ASCENT = 0.905
DESCENT = 0.212

# Global font-size adjustment limits (points, applied to every role above).
FONT_ADJUST_MIN = -3.0
FONT_ADJUST_MAX = 3.0

GRAY = (0.2509804, 0.2509804, 0.2509804)    # #404040 name, headers, employers
BLACK = (0.0, 0.0, 0.0)
LINK_BLUE = (0.01960784, 0.3882353, 0.7568628)  # #0563C1 (Word hyperlink)

# --------------------------------------------------------------------------
# Vertical rhythm: baseline-to-baseline distances at the reference size.
#
# Body line pitch is 11.52 pt (= 8/7 x 10.08, Word "single" spacing for
# Arial). Every gap is modelled as LINE_PITCH + an "extra" amount; when
# content must be squeezed onto the page, the extras are compressed first
# and the line pitch second, so paragraphs keep their texture.
# --------------------------------------------------------------------------
LINE_PITCH = 11.52

GAPS = {
    "line": 11.52,                  # wrapped line inside a paragraph/bullet
    "name_to_contact": 14.88,
    "contact_to_section": 21.84,
    "section_to_paragraph": 15.36,  # SUMMARY -> first summary line
    "headline_to_paragraph": 11.52, # summary headline -> summary text 
    "section_to_entry": 17.04,      # EXPERIENCE/EDUCATION -> first entry
    "section_to_skills": 16.56,     # TECHNICAL SKILLS -> first skill line
    "block_to_section": 24.24,      # last line of a section -> next header
    "heading_to_role": 11.52,       # company line -> title/dates line
    "role_to_bullet": 12.24,        # title line -> first bullet
    "bullet_to_bullet": 12.24,      # last line of bullet -> next bullet
    "entry_to_entry": 22.92,        # last bullet -> next company line
    "school_to_degree": 11.52,
    "edu_to_edu": 18.24,            # degree line -> next school line
    "skill_to_skill": 11.52,
}

# --------------------------------------------------------------------------
# Horizontal elements
# --------------------------------------------------------------------------
RULE_LEFT = 42.48          # section rules overhang the text by 1.44 pt
RULE_RIGHT = 569.52
RULE_OFFSET = 3.12         # rule top is 3.12 pt below the header baseline
RULE_THICKNESS = 0.72

# Bullets are drawn as vector dots matching the reference's Symbol-font bullet
# (measured at 1200 dpi: 3.6 pt diameter, centre 2.82 pt above the baseline,
# centre x = 46.98). Sizes are expressed in ems of the body font so they
# scale with --font-adjust.
BULLET_CENTER_X = 46.98
BULLET_DIAMETER_EM = 0.357
BULLET_RISE_EM = 0.28
BULLET_TEXT_X = 58.12      # hanging indent: wrapped lines align here

UNDERLINE_OFFSET = 1.2     # link underline top, below baseline
UNDERLINE_THICKNESS = 0.72

MIN_COLUMN_GAP = 12.0      # minimum space between left text and a right date

# --------------------------------------------------------------------------
# Fixed structure: section order and titles
# --------------------------------------------------------------------------
SECTION_TITLES = {
    "summary": "SUMMARY",
    "experience": "EXPERIENCE",
    "education": "EDUCATION",
    "skills": "TECHNICAL SKILLS",
}
SECTION_ORDER = ("summary", "experience", "education", "skills")

CONTACT_SEPARATOR = " | "
HEADLINE_SEPARATOR = " | "  
PLACE_SEPARATOR = " \u2013 "    # "Acme Analytics – Austin, TX"
DATE_SEPARATOR = " \u2013 "     # "Oct 2022 – Present"
SKILL_LABEL_SUFFIX = ":"

# --------------------------------------------------------------------------
# Fit-to-page ladder. Tried in order; the first setting that fits wins.
# (extra_scale, leading_scale, auto_shrink_pt)
#   extra_scale   multiplies the "extra" part of every gap above
#   leading_scale multiplies LINE_PITCH (0.95 -> 1.086x line height)
#   auto_shrink   points subtracted from ALL sizes (skipped with --strict)
# --------------------------------------------------------------------------
SPACING_LADDER = (
    [(c, 1.0, 0.0) for c in (1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6)]
    + [(0.6, lead, 0.0) for lead in (0.99, 0.98, 0.97, 0.96, 0.95)]
    + [(c, 0.95, 0.0) for c in (0.55, 0.5)]
)
SHRINK_LADDER = [(0.5, 0.95, -k / 10) for k in range(1, 6)]   # up to -0.5 pt
