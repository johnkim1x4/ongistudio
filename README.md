# ongistudio.app

The website for **Ongi Studio** (온기 스튜디오): a home page with links to the studio's
apps, plus GamLog's app page, privacy policy and support page. Plain static HTML and one
stylesheet, served by GitHub Pages from `main` at <https://ongistudio.app>.

| Path | Page |
|---|---|
| `/` | Studio home: the apps (Split Peak, GamLog), what we care about, why "Ongi", contact |
| `/gamlog/`, `/gamlog/ko/` | GamLog app page, English and Korean ("coming soon to the App Store") |
| `/gamlog/privacy/`, `/gamlog/privacy/ko/` | GamLog privacy policy (the URL for App Store Connect) |
| `/support/` | Support for both apps, with a Korean section at `#ko` (the App Store support URL) |
| `/404.html` | Not-found page (GitHub Pages serves it for missing paths) |

No scripts, cookies, analytics or third-party requests: fonts and images are self-hosted,
and a test enforces it.

## Preview and test

```bash
python3 -m http.server 8737
```

```bash
python3 -m unittest discover -s tests -v
```

The tests (standard library only, also run in CI) check page structure, alt text, that every
internal link and asset exists, that nothing loads from another site, WCAG AA contrast for
every colour token in light and dark, the Korean font subset, and the wording rules below.

## Wording rules (pinned by tests)

- GamLog pages say up front that GamLog doesn't measure blood pressure or diagnose (Apple 1.4.1).
- GamLog pages show no prices and never say "free" / "무료", same as the App Store screenshots.
- No GamLog store link until it's live; then add it and drop "coming soon".
- "HIPAA" never appears.
- The only email addresses on the site are `support@ongistudio.app` and `support@splitpeak.me`.

## Generated files

These scripts live in `scripts/` and read from the GamLog repo checked out next to this one
(`../bp-log`). Rerun them, don't hand-edit their output.

| Script | Writes | Rerun when |
|---|---|---|
| `sync_privacy.py` | `gamlog/privacy/**` from `bp-log/GamLog/Resources/privacy-{en,ko}.md` | the in-app policy changes (also bump the "updated" dates in its `PAGES`) |
| `build_fonts.py` | `assets/fonts/*.woff2`, the Jua Korean subset and `jua-subset.txt` | Korean copy changes (a test fails if a syllable is missing) |
| `make_mark.py` | `assets/img/mark.svg`, `apple-touch-icon.png`, `mark-512.png` | the mark changes |
| `render_og.py` | `assets/img/og/*.png` link previews (headless Chrome) | headline copy changes |

`build_fonts.py` and `make_mark.py` need `pip install fonttools brotli`; `make_mark.py` also
needs `rsvg-convert` (`brew install librsvg`).

Images: app icons and Gami art come from the app repos (Gami is Recraft Pro-plan art, see
`bp-log/docs/ASSETS-PROVENANCE.md`), converted to WebP with `cwebp`. Fonts are SIL OFL 1.1
and their licences ship in `assets/fonts/`.

## Hosting

- GitHub Pages, branch `main`, folder `/`, custom domain in `CNAME`, HTTPS enforced
  (`.app` domains only work over HTTPS).
- DNS at Hover: apex `A`/`AAAA` records to GitHub Pages, `www` CNAME to `johnkim1x4.github.io`,
  and a `_github-pages-challenge-johnkim1x4` TXT record verifying the domain.
