#!/usr/bin/env python3
"""Trace HDDSynthLogoSmall.png into a portable OpenSCAD 2D module.

Emits hddsynth_logo.scad exposing hddsynth_logo() - a 2D shape normalised
so that its width is exactly 100 units, centred on the origin.
Nested contours (disc inside the drive icon, hole inside the disc) are
resolved recursively so holes-within-islands come out right.
"""
import cv2
import numpy as np
from PIL import Image

SRC = "/mnt/user-data/uploads/HDDSynthLogoSmall__2_.png"
DST = "hddsynth_logo.scad"
UPSCALE = 4
EPSILON = 1.4          # polygon simplification, in upscaled pixels

# --- load, flatten any alpha onto white, threshold -----------
im = Image.open(SRC).convert("RGBA")
bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
flat = Image.alpha_composite(bg, im).convert("L")
big = flat.resize((im.width * UPSCALE, im.height * UPSCALE), Image.LANCZOS)
arr = np.array(big)
mask = (arr < 128).astype(np.uint8) * 255      # artwork is dark

contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE,
                                       cv2.CHAIN_APPROX_SIMPLE)
hierarchy = hierarchy[0]
print(f"raw contours: {len(contours)}")

# --- simplify and drop specks -------------------------------
polys = {}
for i, c in enumerate(contours):
    if cv2.contourArea(c) < 12:
        continue
    a = cv2.approxPolyDP(c, EPSILON, True).reshape(-1, 2)
    if len(a) >= 3:
        polys[i] = a
print(f"kept contours: {len(polys)}  points: {sum(len(p) for p in polys.values())}")

# --- normalise: width 100 units, centred, y flipped ----------
W, H = big.width, big.height
scale = 100.0 / W
def fmt(p):
    return "[" + ",".join("[%.3f,%.3f]" % ((x - W/2)*scale, (H/2 - y)*scale)
                          for x, y in p) + "]"

def children(idx):
    out, c = [], hierarchy[idx][2]
    while c != -1:
        if c in polys:
            out.append(c)
        c = hierarchy[c][0]
    return out

def emit(idx, ind):
    """shape(n) = (poly(n) - union(children)) + union(shape(grandchildren))"""
    p = " " * ind
    kids = children(idx)
    if not kids:
        return f"{p}polygon({fmt(polys[idx])});\n"
    s = f"{p}union() {{\n"
    s += f"{p}  difference() {{\n"
    s += f"{p}    polygon({fmt(polys[idx])});\n"
    for k in kids:
        s += f"{p}    polygon({fmt(polys[k])});\n"
    s += f"{p}  }}\n"
    for k in kids:
        for g in children(k):
            s += emit(g, ind + 2)
    s += f"{p}}}\n"
    return s

roots = [i for i in polys if hierarchy[i][3] == -1
         or hierarchy[i][3] not in polys]

body = "".join(emit(r, 4) for r in roots)
aspect = W / H

with open(DST, "w") as f:
    f.write(f"""// ============================================================
//  HDD Synth logo - traced from HDDSynthLogoSmall.png
//  Auto-generated, do not hand-edit.
//  hddsynth_logo() returns a 2D shape 100 units wide,
//  {100/aspect:.3f} units tall, centred on the origin.
// ============================================================

logo_aspect = {aspect:.4f};

module hddsynth_logo() {{
  union() {{
{body}  }}
}}
""")
print(f"roots: {len(roots)}  aspect: {aspect:.4f}  -> {DST}")
