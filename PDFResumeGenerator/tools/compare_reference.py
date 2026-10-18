#!/usr/bin/env python3
"""
Dev tool: compare a generated PDF against the reference PDF line by line.

    python tools/compare_reference.py out.pdf [reference/sample_resume.pdf]

Reports, for every text line: text match, baseline delta, left-x delta, and
font/size of the first character. Requires pdfplumber (requirements-dev.txt).
Useful after editing template.py to confirm fidelity is preserved.
"""
import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REF = ROOT / "reference" / "sample_resume.pdf"


def extract(path):
    rows = []
    with pdfplumber.open(path) as pdf:
        for pno, page in enumerate(pdf.pages):
            for line in page.extract_text_lines(return_chars=True):
                chars = [c for c in line["chars"] if "Symbol" not in c["fontname"]
                         and c["text"] != "\u2022"] or line["chars"]
                c0 = chars[0]
                rows.append({
                    "page": pno + 1,
                    "text": " ".join(line["text"].replace("\u2022", "").split()),
                    "baseline": page.height - c0["matrix"][5],
                    "x": c0["x0"],
                    "font": c0["fontname"].split("+")[-1],
                    "size": round(c0["size"], 2),
                })
    return rows


def main(gen, ref=DEFAULT_REF):
    g, r = extract(gen), extract(ref)
    print(f"reference lines: {len(r)}   generated lines: {len(g)}")
    worst_dy = worst_dx = 0.0
    text_mismatch = 0
    for i in range(max(len(g), len(r))):
        a = r[i] if i < len(r) else None
        b = g[i] if i < len(g) else None
        if not a or not b:
            print(f"{i:3} {'MISSING' if not b else 'EXTRA  '} {(a or b)['text'][:70]}")
            text_mismatch += 1
            continue
        same = a["text"] == b["text"]
        dy, dx = b["baseline"] - a["baseline"], b["x"] - a["x"]
        worst_dy, worst_dx = max(worst_dy, abs(dy)), max(worst_dx, abs(dx))
        text_mismatch += not same
        flag = "  " if same else "!!"
        print(f"{i:3} {flag} dy={dy:+6.2f} dx={dx:+6.2f} {b['size']:5} "
              f"{b['font'][:20]:20} {b['text'][:55]}")
        if not same:
            print(f"        ref: {a['text'][:90]}\n        gen: {b['text'][:90]}")
    print(f"\ntext mismatches: {text_mismatch}   max |dy| = {worst_dy:.2f} pt   "
          f"max |dx| = {worst_dx:.2f} pt")
    return 0 if text_mismatch == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(*sys.argv[1:3]))
