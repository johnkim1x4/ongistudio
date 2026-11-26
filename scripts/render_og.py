"""Render the 1200x630 link-preview images (og:image) with headless Chrome.

    python3 scripts/render_og.py

Writes assets/img/og/{studio,gamlog,gamlog-ko}.png from the cards below, using the
site's own fonts and art. Needs Google Chrome.
"""
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
A = ROOT.as_uri() + "/assets"

FONTS = f"""
@font-face {{ font-family: "Fraunces Soft"; src: url("{A}/fonts/fraunces-soft-semibold.woff2"); font-weight: 600 700; }}
@font-face {{ font-family: "Lexend"; src: url("{A}/fonts/lexend-variable.woff2"); font-weight: 100 900; }}
@font-face {{ font-family: "Jua"; src: url("{A}/fonts/jua-subset.woff2"); }}
@font-face {{ font-family: "Plex"; src: url("{A}/fonts/IBMPlexSans-Bold-Latin1.woff2"); font-weight: 700; }}
@font-face {{ font-family: "Plex"; src: url("{A}/fonts/IBMPlexSans-Regular-Latin1.woff2"); font-weight: 400; }}
html, body {{ margin: 0; width: 1200px; height: 630px; overflow: hidden; }}
body {{ font-family: "Lexend", sans-serif; -webkit-font-smoothing: antialiased; }}
"""

CARDS = {
    "studio": f"""
<style>{FONTS}
body {{ background: #fbf5ec; color: #2b231e; display: flex; flex-direction: column; justify-content: center; padding: 0 96px; box-sizing: border-box; position: relative; }}
body::before {{ content: ""; position: absolute; right: -160px; bottom: -260px; width: 760px; height: 760px; border-radius: 50%; background: radial-gradient(closest-side, #f8d6b3, transparent); }}
img {{ height: 64px; width: auto; position: relative; align-self: flex-start; }}
div {{ position: relative; }}
.k {{ font: 600 26px "Lexend"; letter-spacing: .08em; text-transform: uppercase; color: #6a5a4f; }}
.k span {{ font-family: "Jua"; letter-spacing: 0; text-transform: none; }}
h1 {{ font: 650 76px/1.05 "Fraunces Soft"; margin: 18px 0 22px; letter-spacing: -.01em; }}
p {{ font: 400 30px/1.4 "Lexend"; color: #6a5a4f; margin: 0; }}
</style>
<img src="{A}/img/logo.svg"><div><h1 style="margin-top: 40px">Small apps with a little warmth in them.</h1><p>ongistudio.app · <span style="font-family: Jua">온기 스튜디오</span></p></div>""",
    "splitpeak": f"""
<style>{FONTS}
body {{ background: #0c3e37; color: #fff; padding: 80px 0 0 88px; box-sizing: border-box; position: relative; }}
.id {{ display: flex; align-items: center; gap: 20px; font: 700 40px "Plex"; }}
.id img {{ width: 84px; height: 84px; border-radius: 19px; }}
h1 {{ font: 700 84px/1.04 "Plex"; margin: 44px 0 28px; letter-spacing: -.01em; }}
h1 span {{ color: #f2b632; }}
p {{ font: 400 32px "Plex"; color: rgb(255 255 255 / 85%); margin: 0; }}
.ph {{ position: absolute; right: 70px; top: 60px; width: 300px; padding: 10px; border-radius: 46px; background: #0b201d; transform: rotate(4deg); box-shadow: 0 30px 60px rgb(0 0 0 / 35%); }}
.ph img {{ width: 100%; border-radius: 38px; display: block; }}
</style>
<div class="ph"><img src="{A}/img/splitpeak/screen-settle.webp"></div>
<div class="id"><img src="{A}/img/apps/splitpeak.webp">split peak</div>
<h1>Split the trip,<br><span>settle in one go</span></h1><p>Trips · Roommates · Couples · Dinners</p>""",
    "splitpeak-ko": f"""
<style>{FONTS}
body {{ background: #0c3e37; color: #fff; padding: 80px 0 0 88px; box-sizing: border-box; position: relative; }}
.id {{ display: flex; align-items: center; gap: 20px; font: 700 40px "Plex"; }}
.id img {{ width: 84px; height: 84px; border-radius: 19px; }}
h1 {{ font: 700 80px/1.18 "Plex", "Apple SD Gothic Neo"; margin: 44px 0 28px; letter-spacing: -.01em; }}
h1 span {{ color: #f2b632; }}
p {{ font: 400 32px "Plex", "Apple SD Gothic Neo"; color: rgb(255 255 255 / 85%); margin: 0; }}
.ph {{ position: absolute; right: 70px; top: 60px; width: 300px; padding: 10px; border-radius: 46px; background: #0b201d; transform: rotate(4deg); box-shadow: 0 30px 60px rgb(0 0 0 / 35%); }}
.ph img {{ width: 100%; border-radius: 38px; display: block; }}
</style>
<div class="ph"><img src="{A}/img/splitpeak/screen-settle-ko.webp"></div>
<div class="id"><img src="{A}/img/apps/splitpeak.webp">split peak</div>
<h1>여행도 모임도,<br><span>정산은 한 번에</span></h1><p>더치페이 · 여행 경비 · 모임 정산</p>""",
    "gamlog": f"""
<style>{FONTS}
body {{ background: #dce8e0; color: #22302a; padding: 72px 0 0 88px; box-sizing: border-box; position: relative; }}
.g {{ position: absolute; right: 40px; bottom: -10px; width: 430px; }}
.glow {{ position: absolute; right: -40px; bottom: -120px; width: 620px; height: 620px; border-radius: 50%; background: radial-gradient(closest-side, #fffdf8, transparent); }}
.id {{ display: flex; align-items: center; gap: 20px; }}
.id img {{ width: 84px; height: 84px; border-radius: 19px; box-shadow: 0 6px 18px rgb(0 0 0 / 12%); }}
.id b {{ font: 650 44px "Fraunces Soft"; }} .id i {{ font: normal 34px "Jua"; color: #4b6457; margin-left: 10px; }}
h1 {{ font: 650 70px/1.06 "Fraunces Soft"; margin: 34px 0 30px; max-width: 640px; letter-spacing: -.01em; }}
.pill {{ display: inline-flex; align-items: center; gap: 12px; font: 600 26px "Lexend"; color: #a14817; background: rgb(161 72 23 / 12%); padding: 12px 24px; border-radius: 999px; }}
.pill::before {{ content: ""; width: 12px; height: 12px; border-radius: 50%; background: #e56f2a; }}
</style>
<div class="glow"></div><img class="g" src="{A}/img/gamlog/gami-wave.webp">
<div class="id"><img src="{A}/img/apps/gamlog.webp"><b>GamLog</b><i>감록</i></div>
<h1>The blood pressure log your doctor asked for</h1><span class="pill">Coming soon to the App Store</span>""",
    "gamlog-ko": f"""
<style>{FONTS}
body {{ background: #dce8e0; color: #22302a; padding: 72px 0 0 88px; box-sizing: border-box; position: relative; }}
.g {{ position: absolute; right: 40px; bottom: -10px; width: 430px; }}
.glow {{ position: absolute; right: -40px; bottom: -120px; width: 620px; height: 620px; border-radius: 50%; background: radial-gradient(closest-side, #fffdf8, transparent); }}
.id {{ display: flex; align-items: center; gap: 20px; }}
.id img {{ width: 84px; height: 84px; border-radius: 19px; box-shadow: 0 6px 18px rgb(0 0 0 / 12%); }}
.id b {{ font: normal 48px "Jua"; }} .id i {{ font: 650 32px "Fraunces Soft"; font-style: normal; color: #4b6457; margin-left: 10px; }}
h1 {{ font: normal 72px/1.2 "Jua"; margin: 34px 0 30px; max-width: 620px; word-break: keep-all; }}
.pill {{ display: inline-flex; align-items: center; gap: 12px; font: 600 26px "Lexend"; color: #a14817; background: rgb(161 72 23 / 12%); padding: 12px 24px; border-radius: 999px; }}
.pill span {{ font-family: "Jua"; font-weight: 400; }}
.pill::before {{ content: ""; width: 12px; height: 12px; border-radius: 50%; background: #e56f2a; }}
</style>
<div class="glow"></div><img class="g" src="{A}/img/gamlog/gami-wave.webp">
<div class="id"><img src="{A}/img/apps/gamlog.webp"><b>감록</b><i>GamLog</i></div>
<h1>병원에서 요구하는<br>혈압 일지,<br>간편하게 준비</h1><span class="pill">App Store <span>출시 예정</span></span>""",
}


def main() -> None:
    out = ROOT / "assets/img/og"
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for name, body in CARDS.items():
            page = pathlib.Path(tmp) / f"{name}.html"
            page.write_text(f'<!doctype html><meta charset="utf-8">{body}', encoding="utf-8")
            subprocess.run([
                CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                "--blink-settings=preferredColorScheme=1",  # light: logo.svg follows the colour scheme
                "--allow-file-access-from-files", "--force-device-scale-factor=1",
                "--virtual-time-budget=3000", "--window-size=1200,630",
                f"--screenshot={out / (name + '.png')}", page.as_uri(),
            ], check=True, capture_output=True)
            print("wrote", out / f"{name}.png")


if __name__ == "__main__":
    main()
