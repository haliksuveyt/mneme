#!/usr/bin/env python3
"""Build docs/img/demo.en.svg from docs/img/demo.en.txt (stdlib only).

Transcript format, one line each:
  "# text"  a dim comment line
  "$ cmd"   a command; it is typed character by character
  anything else is output and appears line by line; "…" marks a cut
  an empty line is a short pause

The SVG uses SMIL only: no script, no external fonts, no foreignObject, so it
animates when embedded with <img>. Run: python3 docs/img/build_demo_svg.py
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
SRC = HERE / "demo.en.txt"
OUT = HERE / "demo.en.svg"

W = 1020
FS = 16
CW = 9.6          # advance width per character (enforced with textLength)
LH = 23
PAD_X = 28
TOP = 64
HOLD = 3.0        # seconds the finished screen stays before the loop restarts
TYPE = 0.035      # seconds per typed character
LINE = 0.07       # seconds per revealed output line
FONT = 'ui-monospace, SFMono-Regular, Menlo, Consolas, DejaVu Sans Mono, monospace'


def fmt(x):
    return ("%.4f" % x).rstrip("0").rstrip(".")


def appear(t0, total):
    """opacity 0 until t0, then 1 until the loop restarts."""
    k = min(t0 / total, 0.9999)
    return ('<animate attributeName="opacity" calcMode="discrete" values="0;1;0" '
            'keyTimes="0;%s;1" dur="%ss" repeatCount="indefinite"/>' % (fmt(k), fmt(total)))


def build(lines):
    # schedule
    t = 0.6
    plan = []
    for raw in lines:
        if raw.startswith("$ "):
            n = len(raw)
            plan.append(("cmd", raw, t, n * TYPE))
            t += n * TYPE + 0.5
        elif raw.startswith("# "):
            plan.append(("cmt", raw, t, 0))
            t += 0.5
        elif raw == "":
            plan.append(("gap", raw, t, 0))
            t += 0.7
        else:
            plan.append(("out", raw, t, 0))
            t += LINE
    total = t + HOLD
    nrows = len(plan)
    H = TOP + nrows * LH + 28
    o = []
    o.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
             'role="img" aria-labelledby="t d">' % (W, H, W, H))
    o.append('<title id="t">Mneme terminal demo</title>'
             '<desc id="d">Save a decision, retrieve it with its source path, and produce a handoff packet '
             'for another client.</desc>')
    o.append('<rect width="%d" height="%d" rx="14" fill="#131124"/>' % (W, H))
    o.append('<rect x="1" y="1" width="%d" height="%d" rx="13" fill="none" stroke="#b899ff" stroke-opacity=".25"/>'
             % (W - 2, H - 2))
    o.append('<path d="M1 44H%d" stroke="#b899ff" stroke-opacity=".18"/>' % (W - 1))
    for i, c in enumerate(("#ff6b81", "#ffc857", "#6ee7a8")):
        o.append('<circle cx="%d" cy="23" r="6" fill="%s" fill-opacity=".85"/>' % (28 + i * 22, c))
    o.append('<text x="%d" y="28" fill="#a59abc" font-family="%s" font-size="13" text-anchor="middle">'
             '~/notes &#183; Orbit</text>' % (W // 2, FONT))
    o.append('<g font-family=\'%s\' font-size="%d">'
             % (FONT.replace('"', "&quot;"), FS))
    for idx, (kind, raw, t0, dur) in enumerate(plan):
        y = TOP + idx * LH
        if kind == "gap":
            continue
        if kind == "cmt":
            o.append('<text x="%d" y="%d" fill="#a59abc" opacity="0">%s%s</text>'
                     % (PAD_X, y, escape(raw), appear(t0, total)))
        elif kind == "out":
            lead = len(raw) - len(raw.lstrip(" "))
            raw = raw.lstrip(" ")
            fill = "#a59abc" if raw.strip() == "…" else "#f4f0ff"
            o.append('<text x="%d" y="%d" fill="%s" opacity="0">%s%s</text>'
                     % (PAD_X + lead * CW, y, fill, escape(raw), appear(t0, total)))
        else:
            n = len(raw)
            tw = n * CW
            cid = "c%d" % idx
            steps = n + 1
            wvals = ";".join(fmt(i * CW) for i in range(n + 1)) + ";0"
            xvals = ";".join(fmt(PAD_X + i * CW) for i in range(n + 1)) + ";%s" % fmt(PAD_X)
            ktimes = ";".join(fmt((t0 + i * (dur / n)) / total) for i in range(n + 1)) + ";1"
            # first value (width 0) holds until t0; last (reset) applies at loop end
            ktimes = ";".join([fmt(0)] + ktimes.split(";")[1:])
            wvals2 = "0;" + wvals
            xvals2 = "%s;" % fmt(PAD_X) + xvals
            kt = ["0"] + [fmt((t0 + i * (dur / n)) / total) for i in range(n + 1)] + ["1"]
            o.append('<clipPath id="%s"><rect x="%d" y="%d" height="%d" width="0">'
                     '<animate attributeName="width" calcMode="discrete" values="%s" keyTimes="%s" '
                     'dur="%ss" repeatCount="indefinite"/></rect></clipPath>'
                     % (cid, PAD_X, y - FS, LH + 4, wvals2, ";".join(kt), fmt(total)))
            o.append('<text x="%d" y="%d" fill="#d5c2ff" clip-path="url(#%s)" textLength="%s" '
                     'lengthAdjust="spacing">%s</text>' % (PAD_X, y, cid, fmt(tw), escape(raw)))
            # block cursor while typing
            kt2 = ["0", fmt(t0 / total)] + [fmt((t0 + i * (dur / n)) / total) for i in range(1, n + 1)] + \
                  [fmt(min((t0 + dur + 0.45) / total, 0.9999)), "1"]
            xs = [fmt(PAD_X)] + [fmt(PAD_X + i * CW) for i in range(0, n + 1)] + [fmt(PAD_X + n * CW), fmt(PAD_X)]
            # lengths: kt2 = 2 + n + 2 ; xs = 1 + (n+1) + 2 -> align
            xs = [fmt(PAD_X), fmt(PAD_X)] + [fmt(PAD_X + i * CW) for i in range(1, n + 1)] + \
                 [fmt(PAD_X + n * CW), fmt(PAD_X)]
            ov = ["0", "1"] + ["1"] * n + ["0", "0"]
            assert len(kt2) == len(xs) == len(ov), (len(kt2), len(xs), len(ov))
            o.append('<rect y="%d" width="%s" height="%d" fill="#b899ff" fill-opacity=".8" x="%d" opacity="0">'
                     '<animate attributeName="x" calcMode="discrete" values="%s" keyTimes="%s" dur="%ss" '
                     'repeatCount="indefinite"/>'
                     '<animate attributeName="opacity" calcMode="discrete" values="%s" keyTimes="%s" dur="%ss" '
                     'repeatCount="indefinite"/></rect>'
                     % (y - FS + 2, fmt(CW), FS + 2, PAD_X, ";".join(xs), ";".join(kt2), fmt(total),
                        ";".join(ov), ";".join(kt2), fmt(total)))
    o.append('</g></svg>')
    return "\n".join(o) + "\n", total, nrows


def main():
    lines = SRC.read_text(encoding="utf-8").rstrip("\n").split("\n")
    longest = max(len(l) for l in lines)
    if PAD_X * 2 + longest * CW > W:
        sys.exit("transcript line too wide: %d chars" % longest)
    svg, total, nrows = build(lines)
    ET.fromstring(svg)  # must be well-formed
    OUT.write_text(svg, encoding="utf-8", newline="\n")
    print("wrote %s: %d bytes, %d rows, loop %.1fs (hold %.0fs)" % (OUT.name, len(svg.encode()), nrows, total, HOLD))


if __name__ == "__main__":
    main()
