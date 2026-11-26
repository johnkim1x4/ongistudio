"""Draw the Ongi Studio mark: the Hangul 온 (from Jua, OFL) on a warm ember tile.

Writes assets/img/mark.svg (header logo and favicon) and the PNG sizes iOS and
link previews want. The glyph is converted to a path, so the mark never depends
on a font loading.

    python3 scripts/make_mark.py [path/to/Jua-Regular.ttf]

Needs fontTools (pip install fonttools) and rsvg-convert (brew install librsvg).
"""
import pathlib
import subprocess
import sys

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
JUA = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "bp-log/GamLog/Resources/Fonts/Jua-Regular.ttf"

SIZE = 64          # viewBox
GLYPH_BOX = 36     # the glyph's longer side, in viewBox units
TOP, BOTTOM = "#f2894a", "#d65a24"
CREAM = "#fff8ee"


def glyph_path(char: str) -> str:
    font = TTFont(JUA)
    gs = font.getGlyphSet()
    name = font.getBestCmap()[ord(char)]
    bounds = BoundsPen(gs)
    gs[name].draw(bounds)
    x0, y0, x1, y1 = bounds.bounds
    scale = GLYPH_BOX / max(x1 - x0, y1 - y0)
    w, h = (x1 - x0) * scale, (y1 - y0) * scale
    dx = (SIZE - w) / 2 - x0 * scale
    dy = (SIZE + h) / 2 + y0 * scale + 1  # +1: optical centre sits a touch low
    svg = SVGPathPen(gs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    gs[name].draw(TransformPen(svg, (scale, 0, 0, -scale, dx, dy)))
    return svg.getCommands()


def main() -> None:
    d = glyph_path("온")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" role="img" aria-label="Ongi Studio">
<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{TOP}"/><stop offset="1" stop-color="{BOTTOM}"/></linearGradient></defs>
<rect width="{SIZE}" height="{SIZE}" rx="15" fill="url(#g)"/>
<path fill="{CREAM}" d="{d}"/>
</svg>
"""
    out = ROOT / "assets/img"
    (out / "mark.svg").write_text(svg)
    # Square, full-bleed versions for iOS home screen (it rounds the corners itself).
    flat = svg.replace('rx="15"', 'rx="0"')
    (out / "mark-flat.svg").write_text(flat)
    for name, src, px in [("apple-touch-icon.png", "mark-flat.svg", 180), ("mark-512.png", "mark.svg", 512)]:
        subprocess.run(["rsvg-convert", "-w", str(px), "-h", str(px), "-o", str(out / name), str(out / src)], check=True)
    (out / "mark-flat.svg").unlink()
    print("wrote", out / "mark.svg", "and PNGs")


if __name__ == "__main__":
    main()
