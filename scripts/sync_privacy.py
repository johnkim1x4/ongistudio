"""Build the GamLog privacy pages from the app's own policy text.

The app bundles GamLog/Resources/privacy-{en,ko,ja}.md (bp-log repo). This script turns
those files, and health-data-en.md (the Consumer Health Data Privacy Policy that
Washington's My Health My Data Act wants as its own page), into HTML under
gamlog/privacy/, so the in-app policy and the hosted one are the same words.
tests/test_site.py fails if the pages drift from the source (when the bp-log checkout
sits next to this repo).

    python3 scripts/sync_privacy.py            # write the pages
    python3 scripts/sync_privacy.py --check    # exit 1 if they are out of date

Source format (also what the app shows, as inline Markdown):
  block 1          the title (the page's h1 comes from PAGES)
  block 2          "Last updated: ..." / "최종 수정일: ..." / "最終更新日：..."
  **Heading**      a block that is only bold text becomes an h2
  - item           a block of "- " lines becomes a list
  anything else    a paragraph; **bold** and [text](https://... or mailto:...) work inline
"""
import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT.parent / "bp-log/GamLog/Resources"

PAGES = {
    "en": {
        "lang": "en",
        "src": "privacy-en.md",
        "out": "gamlog/privacy/index.html",
        "title": "GamLog Privacy Policy",
        "h1": "GamLog privacy policy",
        "description": "GamLog keeps your blood pressure notebook on your iPhone. No account, no server, no analytics, no advertising.",
        "url": "https://ongistudio.app/gamlog/privacy/",
        "alternates": True,
        "other": ("/gamlog/privacy/ko/", "ko", "한국어"),
        "skip": "Skip to content",
        "nav": [("/gamlog/", "GamLog"), ("/support/", "Support")],
        "footer": "© 2026 Ongi Studio · No cookies, no analytics.",
    },
    "ko": {
        "lang": "ko",
        "src": "privacy-ko.md",
        "out": "gamlog/privacy/ko/index.html",
        "title": "감록 개인정보 처리방침",
        "h1": "감록 개인정보 처리방침",
        "description": "감록은 혈압 수첩을 iPhone 안에만 저장합니다. 회원가입, 서버, 분석 도구, 광고가 없습니다.",
        "url": "https://ongistudio.app/gamlog/privacy/ko/",
        "alternates": True,
        "other": ("/gamlog/privacy/", "en", "English"),
        "skip": "본문으로 건너뛰기",
        "nav": [("/gamlog/ko/", "감록"), ("/support/#ko", "고객 지원")],
        "footer": "© 2026 Ongi Studio · 쿠키와 분석 도구를 쓰지 않아요.",
    },
    "ja": {
        "lang": "ja",
        "src": "privacy-ja.md",
        "out": "gamlog/privacy/ja/index.html",
        "title": "柿ログ プライバシーポリシー",
        "h1": "柿ログ プライバシーポリシー",
        "description": "柿ログは血圧手帳をあなたのiPhoneの中にだけ保存します。アカウント、サーバー、分析ツール、広告はありません。",
        "url": "https://ongistudio.app/gamlog/privacy/ja/",
        "alternates": True,
        "other": ("/gamlog/privacy/", "en", "English"),
        "skip": "本文へスキップ",
        "nav": [("/gamlog/", "GamLog"), ("/support/", "サポート")],
        "footer": "© 2026 Ongi Studio · Cookieや分析ツールは使っていません。",
    },
    "health": {
        "lang": "en",
        "src": "health-data-en.md",
        "out": "gamlog/privacy/health-data/index.html",
        "title": "GamLog Consumer Health Data Privacy Policy",
        "h1": "GamLog Consumer Health Data Privacy Policy",
        "description": "How GamLog handles consumer health data under Washington's My Health My Data Act and similar state laws.",
        "url": "https://ongistudio.app/gamlog/privacy/health-data/",
        "alternates": False,
        "other": None,
        "skip": "Skip to content",
        "nav": [("/gamlog/", "GamLog"), ("/support/", "Support")],
        "footer": "© 2026 Ongi Studio · No cookies, no analytics.",
    },
}

HEADING = re.compile(r"^\*\*(?P<text>[^*]+)\*\*$")
UPDATED = re.compile(r"^(Last updated:|최종 수정일:|最終更新日：)")
LINK = re.compile(r"\[(?P<text>[^\]]+)\]\((?P<url>(?:https://|mailto:)[^)\s]+)\)")
BOLD = re.compile(r"\*\*(?P<text>[^*]+)\*\*")


def inline(text: str) -> str:
    """Escape, then turn [text](url) and **bold** into HTML. Only https and mailto links."""
    out, pos = [], 0
    for m in LINK.finditer(text):
        out.append(html.escape(text[pos:m.start()], quote=False))
        url = m["url"].replace("https://ongistudio.app/", "/")
        out.append(f'<a href="{html.escape(url)}">{html.escape(m["text"], quote=False)}</a>')
        pos = m.end()
    out.append(html.escape(text[pos:], quote=False))
    joined = "".join(out)
    if "](" in LINK.sub("", text):
        raise ValueError(f"only https:// and mailto: links are allowed: {text!r}")
    return BOLD.sub(lambda m: f"<strong>{m['text']}</strong>", joined)


def blocks(md: str) -> list[str]:
    return [b.strip() for b in md.strip().split("\n\n") if b.strip()]


def updated_line(md: str) -> str:
    second = blocks(md)[1]
    if not UPDATED.match(second):
        raise ValueError("the second block must be the 'Last updated' / '최종 수정일' / '最終更新日' line")
    return second


def body_html(md: str) -> str:
    parts = []
    for block in blocks(md)[2:]:
        lines = block.split("\n")
        if (m := HEADING.match(block)):
            parts.append(f"    <h2>{html.escape(m['text'].rstrip('.').strip(), quote=False)}</h2>")
        elif all(line.startswith("- ") for line in lines):
            items = "\n".join(f"      <li>{inline(line[2:].strip())}</li>" for line in lines)
            parts.append(f"    <ul>\n{items}\n    </ul>")
        else:
            parts.append(f"    <p>{inline(' '.join(line.strip() for line in lines))}</p>")
    return "\n".join(parts)


def render(key: str, md: str) -> str:
    p = PAGES[key]
    lang = p["lang"]
    body = body_html(md)
    updated = html.escape(updated_line(md), quote=False)
    nav = "\n".join(f'      <li><a href="{h}">{t}</a></li>' for h, t in p["nav"])
    switch = ""
    if p["other"]:
        other_href, other_lang, other_label = p["other"]
        switch = f'\n      <li><a class="lang-switch" href="{other_href}" lang="{other_lang}" hreflang="{other_lang}">{other_label}</a></li>'
    alternates = ("""
<link rel="alternate" hreflang="en" href="https://ongistudio.app/gamlog/privacy/">
<link rel="alternate" hreflang="ko" href="https://ongistudio.app/gamlog/privacy/ko/">
<link rel="alternate" hreflang="ja" href="https://ongistudio.app/gamlog/privacy/ja/">""" if p["alternates"] else "")
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{p["title"]}</title>
<meta name="description" content="{p["description"]}">
<link rel="canonical" href="{p["url"]}">{alternates}
<link rel="icon" href="/assets/img/mark.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<meta name="theme-color" content="#dce8e0" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#131b17" media="(prefers-color-scheme: dark)">
<link rel="stylesheet" href="/assets/css/site.css">
</head>
<body class="theme-gamlog">
<!-- Generated by scripts/sync_privacy.py from bp-log/GamLog/Resources/{p["src"]}. Edit the source, not this file. -->
<a class="skip" href="#main">{p["skip"]}</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="/" aria-label="Ongi Studio"><img class="brand-mark" src="/assets/img/mark.svg" alt="" width="36" height="36"><img class="brand-word" src="/assets/img/logo.svg" alt="" width="149" height="30"></a>
    <nav aria-label="Main"><ul class="nav">
{nav}{switch}
    </ul></nav>
  </div>
</header>

<main id="main" class="doc">
  <div class="narrow">
    <h1>{p["h1"]}</h1>
    <p class="updated">{updated}</p>
{body}
  </div>
</main>

<footer class="site-footer">
  <div class="wrap">
    <p>{p["footer"]}</p>
    <ul>
      <li><a href="/" lang="en">Ongi Studio</a></li>
{nav}
    </ul>
  </div>
</footer>
</body>
</html>
"""


def build(check: bool = False) -> list[str]:
    """Write (or, with check, compare) each page. Returns the pages that are out of date."""
    stale = []
    for key, p in PAGES.items():
        src = SOURCE / p["src"]
        out = ROOT / p["out"]
        want = render(key, src.read_text(encoding="utf-8"))
        have = out.read_text(encoding="utf-8") if out.exists() else ""
        if want != have:
            stale.append(p["out"])
            if not check:
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(want, encoding="utf-8")
    return stale


if __name__ == "__main__":
    check = "--check" in sys.argv
    stale = build(check=check)
    if check and stale:
        sys.exit("out of date: " + ", ".join(stale) + " (run scripts/sync_privacy.py)")
    print("up to date" if not stale else "wrote " + ", ".join(stale))
