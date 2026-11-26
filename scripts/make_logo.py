"""Draw the Ongi Studio logo: the "ongi studio" wordmark whose first i-dot is an app tile.

Interim logo (chosen 2026-11-26, round 2 option 5) until a final mark is decided.

Writes, from Fraunces Soft SemiBold (OFL) outlines, so nothing depends on a font loading:
- assets/img/logo.svg          header wordmark; switches ink for dark mode by itself
- assets/img/mark.svg          favicon: the tile-dotted ı on a cream app tile
- assets/img/apple-touch-icon.png (180 px, full bleed) and mark-512.png

    python3 scripts/make_logo.py [path/to/FrauncesSoft-SemiBold.ttf]

Needs fontTools (pip install fonttools) and rsvg-convert (brew install librsvg).
"""
import pathlib
import subprocess
import sys

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "bp-log/GamLog/Resources/Fonts/FrauncesSoft-SemiBold.ttf"
OUT = ROOT / "assets/img"

TEXT = "ongı studio"   # dotless ı: its dot is the app tile
TRACKING = -20               # font units (of 2000), about -0.01em, as on the canvas
TILE_SCALE = 1.35            # tile size relative to Fraunces' own i-dot
TILE_GAP = 110               # font units of clear space between the tile and the top of the ı
INK, INK_DARK = "#2b231e", "#f5ece3"
TILE = ("#f2894a", "#d65a24")
TILE_DARK = ("#f2a672", "#e8743b")
CREAM, CREAM_LINE = "#fffdf8", "#eaded0"


def fmt(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


def i_dot_box(font, gs):
    """Centre and size of the dot on Fraunces' own 'i', in font units."""
    rec = DecomposingRecordingPen(gs)
    gs[font.getBestCmap()[ord("i")]].draw(rec)
    xh = font["OS/2"].sxHeight
    contours, cur = [], []
    for op, args in rec.value:
        cur.append((op, args))
        if op in ("closePath", "endPath"):
            contours.append(cur)
            cur = []
    for c in contours:
        pts = [p for _, args in c for p in args]
        if pts and min(y for _, y in pts) > xh:
            xs, ys = [x for x, _ in pts], [y for _, y in pts]
            return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(max(xs) - min(xs), max(ys) - min(ys))
    raise SystemExit("could not find the i-dot")


def run(font, gs, text):
    """Each glyph's name and pen-x position along the line."""
    cmap, hmtx = font.getBestCmap(), font["hmtx"]
    x, out = 0, []
    for ch in text:
        name = cmap[ord(ch)]
        out.append((name, x))
        x += hmtx[name][0] + TRACKING
    return out


def draw(gs, placed, flip_y):
    """SVG path data and bounds for glyphs placed at (name, x), y flipped about flip_y."""
    svg = SVGPathPen(gs, ntos=fmt)
    bounds = BoundsPen(gs)
    for name, x in placed:
        t = (1, 0, 0, -1, x, flip_y)
        gs[name].draw(TransformPen(svg, t))
        gs[name].draw(TransformPen(bounds, t))
    return svg.getCommands(), bounds.bounds


def tile_rect(cx, cy, size):
    r = size * 0.3
    return f'x="{fmt(cx - size / 2)}" y="{fmt(cy - size / 2)}" width="{fmt(size)}" height="{fmt(size)}" rx="{fmt(r)}"'


def main() -> None:
    font = TTFont(FONT)
    gs = font.getGlyphSet()
    asc = font["hhea"].ascent
    dot_cx, dot_cy, dot_size = i_dot_box(font, gs)
    tile = dot_size * TILE_SCALE
    stem = BoundsPen(gs)
    gs["dotlessi"].draw(stem)
    dot_cy = max(dot_cy, stem.bounds[3] + TILE_GAP + tile / 2)  # never let the tile touch the stem

    # Wordmark
    placed = run(font, gs, TEXT)
    d, (x0, y0, x1, y1) = draw(gs, placed, asc)
    ix = next(x for n, x in placed if n == "dotlessi")
    tcx, tcy = ix + dot_cx, asc - dot_cy
    top = min(y0, tcy - tile / 2)
    pad = 20
    vb = (x0 - pad, top - pad, (x1 - x0) + 2 * pad, (y1 - top) + 2 * pad)
    logo = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="{' '.join(fmt(v) for v in vb)}" role="img" aria-label="Ongi Studio">
<style>.ink{{fill:{INK}}}.t1{{stop-color:{TILE[0]}}}.t2{{stop-color:{TILE[1]}}}@media (prefers-color-scheme: dark){{.ink{{fill:{INK_DARK}}}.t1{{stop-color:{TILE_DARK[0]}}}.t2{{stop-color:{TILE_DARK[1]}}}}}</style>
<defs><linearGradient id="t" x1="0" y1="0" x2="0" y2="1"><stop offset="0" class="t1"/><stop offset="1" class="t2"/></linearGradient></defs>
<path class="ink" d="{d}"/>
<rect {tile_rect(tcx, tcy, tile)} fill="url(#t)"/>
</svg>
"""
    (OUT / "logo.svg").write_text(logo)
    ratio = vb[2] / vb[3]

    # Icon: the tile-dotted ı alone, centred on a cream app tile
    d_i, (ix0, iy0, ix1, iy1) = draw(gs, [("dotlessi", 0)], asc)
    gcx, gcy = dot_cx, asc - dot_cy
    top_i = min(iy0, gcy - tile / 2)
    group_w = max(ix1, gcx + tile / 2) - min(ix0, gcx - tile / 2)
    group_h = iy1 - top_i
    s = 40 / group_h
    left = min(ix0, gcx - tile / 2)
    tx = 32 - (left + group_w / 2) * s
    ty = 32 - (top_i + group_h / 2) * s
    def icon(rx, stroke):
        line = f' stroke="{CREAM_LINE}" stroke-width="2"' if stroke else ""
        inset = 1 if stroke else 0
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="Ongi Studio">
<defs><linearGradient id="t" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{TILE[0]}"/><stop offset="1" stop-color="{TILE[1]}"/></linearGradient></defs>
<rect x="{inset}" y="{inset}" width="{64 - 2 * inset}" height="{64 - 2 * inset}" rx="{rx}" fill="{CREAM}"{line}/>
<g transform="translate({fmt(tx)} {fmt(ty)}) scale({s:.5f})"><path fill="{INK}" d="{d_i}"/><rect {tile_rect(gcx, gcy, tile)} fill="url(#t)"/></g>
</svg>
"""
    (OUT / "mark.svg").write_text(icon(15, True))
    flat = OUT / "mark-flat.svg"
    flat.write_text(icon(0, False))
    for name, src, px in [("apple-touch-icon.png", flat, 180), ("mark-512.png", OUT / "mark.svg", 512)]:
        subprocess.run(["rsvg-convert", "-w", str(px), "-h", str(px), "-o", str(OUT / name), str(src)], check=True)
    flat.unlink()
    print(f"wrote logo.svg (aspect {ratio:.3f}), mark.svg and PNGs")


if __name__ == "__main__":
    main()
