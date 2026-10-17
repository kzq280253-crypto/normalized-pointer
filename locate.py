# -*- coding: utf-8 -*-
"""
Find a colored round marker in a screenshot and report where it is, in
normalized coordinates.

Written for verifying on-screen pointer overlays, but it works for any
solid-colored circular badge.

Pitfall #3 -- the label bubble lies.
    Overlay pointers usually come with a text label drawn in the *same* color
    as the badge. If you segment the image by color and take the bounding box,
    the bubble merges with the badge and drags its center sideways. Measured on
    a real overlay: a 78px badge plus a 130px bubble produced a center that was
    off by 40 logical pixels -- enough to conclude "the app has a bug" when it
    did not.

    The fix here: the badge is round, so every column through it spans nearly
    the full diameter; the bubble is flat, so its columns span only its text
    height. Keep only columns whose vertical span is large, and the bubble
    filters itself out.
"""
from collections import defaultdict

from PIL import Image

MIN_COL_SPAN = 45.0      # a column must span at least this many px to count
SIZE_RANGE = (50, 115)   # plausible diameter range for the badge


def find_marker(path, rgb, tolerance=16, min_col_span=MIN_COL_SPAN,
                size_range=SIZE_RANGE, verbose=False):
    """Return ((nx, ny), meta) for the marker, or (None, meta) if not found.

    rgb        -- the marker's fill color, sampled once from a screenshot
    tolerance  -- per-channel tolerance; keep it tight or you will pick up
                  unrelated UI accents of a similar blue
    """
    im = Image.open(path).convert("RGB")
    W, H = im.size
    px = im.load()

    tr, tg, tb = rgb
    pts = []
    for y in range(H):
        for x in range(W):
            r, g, b = px[x, y]
            if abs(r - tr) < tolerance and abs(g - tg) < tolerance and abs(b - tb) < tolerance:
                pts.append((x, y))
    meta = {"image_size": (W, H), "matched_pixels": len(pts)}
    if not pts:
        return None, meta

    col_y = defaultdict(list)
    for x, y in pts:
        col_y[x].append(y)

    kept = [(x, ys) for x, ys in col_y.items()
            if (max(ys) - min(ys)) >= min_col_span]
    if not kept:
        return None, meta

    xs = [x for x, _ in kept]
    ys_all = [y for _, ys in kept for y in ys]
    cx = (min(xs) + max(xs)) / 2.0
    cy = (min(ys_all) + max(ys_all)) / 2.0
    w, h = max(xs) - min(xs), max(ys_all) - min(ys_all)

    meta.update({"center_px": (cx, cy), "bbox": (w, h)})
    lo, hi = size_range
    if not (lo <= w <= hi and lo <= h <= hi):
        meta["rejected"] = "bbox %dx%d outside %s" % (w, h, size_range)
        return None, meta

    return ((cx / W * 1000.0, cy / H * 1000.0), meta)


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "screen.png"
    found, meta = find_marker(path, (56, 128, 239), verbose=True)
    print("image:", meta["image_size"], "matched px:", meta["matched_pixels"])
    if found is None:
        print("not found:", meta.get("rejected", "no colored pixels"))
        raise SystemExit(1)
    print("normalized: x=%.1f y=%.1f  bbox=%s" % (found[0], found[1], meta["bbox"]))
