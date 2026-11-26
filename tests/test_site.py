"""Checks for the static site. Standard library only:  python3 -m unittest -v"""
import html.parser
import importlib.util
import pathlib
import re
import unittest
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://ongistudio.app"
PAGES = sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts and "scripts" not in p.parts)
INDEXABLE = [p for p in PAGES if p.name == "index.html"]
GAMLOG_EN = [ROOT / "gamlog/index.html", ROOT / "gamlog/privacy/index.html"]
GAMLOG_KO = [ROOT / "gamlog/ko/index.html", ROOT / "gamlog/privacy/ko/index.html"]
SUPPORT_EMAIL = "support@ongistudio.app"
# The only addresses allowed anywhere on the public site. A personal address must never leak.
PUBLIC_EMAILS = {SUPPORT_EMAIL, "support@splitpeak.me"}


class Page(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []      # (tag, attrs dict)
        self.text = []
        self.h1 = 0
        self.html_lang = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if tag == "h1":
            self.h1 += 1
        if tag == "html":
            self.html_lang = a.get("lang")

    handle_startendtag = handle_starttag

    def handle_data(self, data):
        self.text.append(data)

    def find(self, tag, **want):
        return [a for t, a in self.tags if t == tag and all(a.get(k) == v for k, v in want.items())]

    def meta(self, key, value):
        found = [a.get("content") for t, a in self.tags if t == "meta" and a.get(key) == value]
        return found[0] if found else None

    @property
    def plain(self):
        return re.sub(r"\s+", " ", " ".join(self.text))


def parse(path):
    p = Page()
    p.feed(path.read_text(encoding="utf-8"))
    return p


def site_path(url: str, page: pathlib.Path):
    """Map a same-site URL to the file that serves it, or None for other sites."""
    u = urlparse(url)
    if u.scheme in ("mailto", "tel"):
        return None
    if u.scheme or u.netloc:
        if f"{u.scheme}://{u.netloc}" != SITE:
            return None
        path = u.path
    elif url.startswith("#") or not url:
        return None
    elif url.startswith("/"):
        path = u.path
    else:
        path = "/" + str((page.parent / u.path).resolve().relative_to(ROOT))
    target = ROOT / path.lstrip("/")
    return target / "index.html" if path.endswith("/") else target


def norm(s: str) -> str:
    return s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')


class Structure(unittest.TestCase):
    def test_every_page_has_the_basics(self):
        for page in PAGES:
            with self.subTest(page=page.relative_to(ROOT)):
                p = parse(page)
                self.assertIn(p.html_lang, ("en", "ko"))
                self.assertTrue(p.find("title"), "title")
                self.assertTrue(p.meta("name", "description"), "meta description")
                self.assertIn("width=device-width", p.meta("name", "viewport") or "")
                self.assertTrue(p.find("link", rel="icon"), "favicon")
                self.assertTrue(p.find("link", rel="stylesheet", href="/assets/css/site.css"))
                self.assertEqual(p.h1, 1, "exactly one h1")
                self.assertTrue(p.find("a", **{"class": "skip", "href": "#main"}), "skip link")
                self.assertTrue([a for t, a in p.tags if a.get("id") == "main"], "#main target")

    def test_indexable_pages_have_canonical_and_previews(self):
        for page in INDEXABLE:
            with self.subTest(page=page.relative_to(ROOT)):
                p = parse(page)
                canon = p.find("link", rel="canonical")
                rel = page.parent.relative_to(ROOT).as_posix()
                expected = SITE + "/" + ("" if rel == "." else rel + "/")
                self.assertEqual(canon[0]["href"] if canon else None, expected)

    def test_link_previews_point_at_real_images(self):
        for page in INDEXABLE:
            p = parse(page)
            img = p.meta("property", "og:image")
            if page.parent.name == "privacy" or page.parent.parent.name == "privacy":
                continue
            with self.subTest(page=page.relative_to(ROOT)):
                self.assertTrue(img, "og:image")
                self.assertTrue(site_path(img, page).exists(), img)

    def test_images_have_alt_and_size(self):
        for page in PAGES:
            for a in parse(page).find("img"):
                with self.subTest(page=page.relative_to(ROOT), src=a.get("src")):
                    self.assertIn("alt", a, "alt attribute (empty is fine when decorative)")
                    self.assertTrue(a.get("width") and a.get("height"), "width/height to avoid layout shift")

    def test_404_is_not_indexed(self):
        self.assertEqual(parse(ROOT / "404.html").meta("name", "robots"), "noindex")

    def test_cname_and_no_jekyll(self):
        self.assertEqual((ROOT / "CNAME").read_text().strip(), "ongistudio.app")
        self.assertTrue((ROOT / ".nojekyll").exists())

    def test_sitemap_lists_every_indexable_page(self):
        sitemap = (ROOT / "sitemap.xml").read_text()
        for page in INDEXABLE:
            rel = page.parent.relative_to(ROOT).as_posix()
            url = SITE + "/" + ("" if rel == "." else rel + "/")
            self.assertIn(f"<loc>{url}</loc>", sitemap)


class Links(unittest.TestCase):
    def test_every_internal_link_and_asset_exists(self):
        for page in PAGES:
            p = parse(page)
            for tag, a in p.tags:
                for attr in ("href", "src"):
                    url = a.get(attr)
                    if not url:
                        continue
                    target = site_path(url, page)
                    if target is None:
                        continue
                    with self.subTest(page=page.relative_to(ROOT), url=url):
                        self.assertTrue(target.exists(), f"{url} -> {target}")

    def test_css_urls_exist(self):
        css = (ROOT / "assets/css/site.css").read_text()
        for url in re.findall(r'url\("([^"]+)"\)', css):
            with self.subTest(url=url):
                self.assertTrue(url.startswith("/"), "fonts are self-hosted")
                self.assertTrue((ROOT / url.lstrip("/")).exists(), url)

    def test_nothing_loads_from_other_sites(self):
        """No third-party scripts, styles, fonts or images: the site sets no cookies and tracks nothing."""
        for page in PAGES:
            p = parse(page)
            for tag, a in p.tags:
                url = (a.get("src") if tag in ("img", "script", "iframe", "source") else
                       a.get("href") if tag == "link" and a.get("rel") not in ("canonical", "alternate") else None)
                if url:
                    with self.subTest(page=page.relative_to(ROOT), url=url):
                        self.assertTrue(url.startswith("/"), url)
            self.assertFalse(p.find("script"), f"{page}: no scripts")

    def test_language_versions_point_at_each_other(self):
        pairs = [(ROOT / "gamlog/index.html", "/gamlog/ko/"), (ROOT / "gamlog/ko/index.html", "/gamlog/"),
                 (ROOT / "gamlog/privacy/index.html", "/gamlog/privacy/ko/"),
                 (ROOT / "gamlog/privacy/ko/index.html", "/gamlog/privacy/")]
        for page, other in pairs:
            with self.subTest(page=page.relative_to(ROOT)):
                self.assertTrue(parse(page).find("a", **{"class": "lang-switch", "href": other}))


class Wording(unittest.TestCase):
    """Policy decisions, pinned so a later edit can't quietly undo them."""

    def test_only_public_support_addresses_appear(self):
        found = set()
        for f in ROOT.rglob("*"):
            if f.is_file() and ".git" not in f.parts and f.suffix in (".html", ".xml", ".txt", ".css", ".md"):
                found |= set(re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", f.read_text(encoding="utf-8", errors="ignore")))
        self.assertLessEqual(found - {"noreply@anthropic.com"}, PUBLIC_EMAILS)

    def test_support_email_is_on_every_content_page(self):
        for page in INDEXABLE:
            with self.subTest(page=page.relative_to(ROOT)):
                self.assertIn(f"mailto:{SUPPORT_EMAIL}", page.read_text())

    def test_gamlog_says_it_does_not_measure_or_diagnose(self):
        # Apple 1.4.1 / FDA wellness line: the disclaimer leads, in both languages.
        for page in GAMLOG_EN:
            self.assertRegex(norm(parse(page).plain), r"(doesn't|does not) measure blood pressure")
        for page in GAMLOG_KO:
            self.assertRegex(parse(page).plain, r"(혈압을 재거나 진단하지 않|혈압을 측정하거나 진단하지 않)")

    def test_gamlog_pages_name_no_price_and_never_say_free(self):
        # Copy rule from the App Store slides: people find out about pricing in the app.
        for page in [ROOT / "gamlog/index.html", ROOT / "gamlog/ko/index.html"]:
            text = parse(page).plain
            with self.subTest(page=page.relative_to(ROOT)):
                self.assertNotRegex(text, r"[$₩]\s?\d|\d\s?원\b|\d+\.99")
                self.assertNotRegex(text.lower(), r"\bfree\b|무료")

    def test_never_mentions_hipaa(self):
        for page in PAGES:
            self.assertNotIn("hipaa", page.read_text().lower(), page)

    def test_gamlog_is_announced_as_coming_soon_without_a_store_link(self):
        en, ko = parse(ROOT / "gamlog/index.html"), parse(ROOT / "gamlog/ko/index.html")
        self.assertIn("Coming soon to the App Store", en.plain)
        self.assertIn("출시 예정", ko.plain)
        for p in (en, ko):
            self.assertFalse([a for t, a in p.tags if "apps.apple.com" in a.get("href", "")],
                             "add the store link when GamLog is live, and drop 'coming soon'")

    def test_home_links_both_apps(self):
        home = (ROOT / "index.html").read_text()
        self.assertIn('href="https://www.splitpeak.me/"', home)
        self.assertIn('href="/gamlog/"', home)


class Fonts(unittest.TestCase):
    def test_jua_subset_covers_every_hangul_syllable_on_the_site(self):
        covered = set((ROOT / "assets/fonts/jua-subset.txt").read_text(encoding="utf-8").strip())
        used = set()
        for page in PAGES:
            used |= set(re.findall(r"[가-힣]", page.read_text(encoding="utf-8")))
        self.assertFalse(used - covered, "run scripts/build_fonts.py to refresh the Korean subset")

    def test_font_licences_ship_with_the_fonts(self):
        for lic in ("Fraunces-OFL.txt", "Lexend-OFL.txt", "Jua-OFL.txt"):
            self.assertTrue((ROOT / "assets/fonts" / lic).exists(), lic)


def _hex(c):
    c = c.lstrip("#")
    return [int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def _lum(c):
    ch = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in _hex(c)]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


class Contrast(unittest.TestCase):
    """Every text/background token pair passes WCAG AA (4.5:1) in all four palettes."""

    def palettes(self):
        css = (ROOT / "assets/css/site.css").read_text()
        blocks = re.findall(r"(:root|\.theme-gamlog)\s*\{([^}]*)\}", css)
        out = {}
        for i, (sel, body) in enumerate(blocks):
            name = f"{sel}#{i}"
            out[name] = dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", body))
        return out

    def test_pairs(self):
        header = (ROOT / "assets/css/site.css").read_text().split("*/", 1)[0]
        pairs = [p.split("/") for p in re.search(r"CONTRAST:(.*)", header).group(1).split()]
        palettes = self.palettes()
        self.assertEqual(len(palettes), 4, "studio and GamLog, light and dark")
        for name, tokens in palettes.items():
            for fg, bg in pairs:
                with self.subTest(palette=name, pair=f"{fg}/{bg}"):
                    self.assertGreaterEqual(contrast(tokens[fg], tokens[bg]), 4.5)


class PrivacySource(unittest.TestCase):
    def test_privacy_pages_match_the_apps_policy_text(self):
        spec = importlib.util.spec_from_file_location("sync_privacy", ROOT / "scripts/sync_privacy.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not mod.SOURCE.exists():
            self.skipTest("bp-log checkout not next to this repo")
        self.assertEqual(mod.build(check=True), [], "run scripts/sync_privacy.py")

    def test_privacy_pages_fill_in_the_contact(self):
        for page in GAMLOG_EN + GAMLOG_KO:
            if "privacy" in page.parts:
                text = page.read_text()
                self.assertIn(f"mailto:{SUPPORT_EMAIL}", text)
                self.assertNotIn("[contact address to be added]", text)
                self.assertNotIn("[문의처 추가 예정]", text)
                self.assertNotIn("draft", text.lower())


if __name__ == "__main__":
    unittest.main()
