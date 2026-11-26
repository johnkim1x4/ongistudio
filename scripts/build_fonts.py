"""Make the site's self-hosted web fonts (no third-party font requests).

- Fraunces Soft SemiBold and Lexend (variable): converted to WOFF2 as they are.
- Jua: subset to ASCII plus every Hangul syllable used on the site's pages, so the
  Korean headings load in a few kilobytes. The characters it covers are written to
  assets/fonts/jua-subset.txt; tests/test_site.py fails if a page uses Hangul that
  the subset is missing. After changing Korean copy, rerun this script.

    python3 scripts/build_fonts.py [path/to/bp-log/GamLog/Resources/Fonts]

Needs: pip install fonttools brotli. All three fonts are SIL OFL 1.1; their licence
texts are copied next to the WOFF2 files. (Pretendard is not used here: its Reserved
Font Name forbids subsetting, and the full files are 1.5 MB each.)
"""
import pathlib
import re
import shutil
import sys

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "bp-log/GamLog/Resources/Fonts"
OUT = ROOT / "assets/fonts"
HANGUL = re.compile(r"[가-힣]")


def site_hangul() -> str:
    chars = set()
    for page in ROOT.rglob("*.html"):
        if ".git" in page.parts or "scripts" in page.parts:
            continue
        chars.update(HANGUL.findall(page.read_text(encoding="utf-8")))
    return "".join(sorted(chars))


def to_woff2(src: pathlib.Path, dst: pathlib.Path) -> None:
    font = TTFont(src)
    font.flavor = "woff2"
    font.save(dst)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    to_woff2(SRC / "FrauncesSoft-SemiBold.ttf", OUT / "fraunces-soft-semibold.woff2")
    to_woff2(SRC / "Lexend-Variable.ttf", OUT / "lexend-variable.woff2")

    hangul = site_hangul()
    text = "".join(chr(c) for c in range(0x20, 0x7F)) + "·…‘’“”–—" + hangul
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    font = subset.load_font(str(SRC / "Jua-Regular.ttf"), opts)
    sub = subset.Subsetter(opts)
    sub.populate(text=text)
    sub.subset(font)
    subset.save_font(font, str(OUT / "jua-subset.woff2"), opts)
    (OUT / "jua-subset.txt").write_text(hangul + "\n", encoding="utf-8")

    for lic in ["Fraunces-OFL.txt", "Lexend-OFL.txt", "Jua-OFL.txt"]:
        shutil.copy(SRC / lic, OUT / lic)
    for f in sorted(OUT.iterdir()):
        print(f"{f.stat().st_size / 1024:7.1f} KB  {f.name}")
    print(f"Jua subset covers {len(hangul)} Hangul syllables")


if __name__ == "__main__":
    main()
