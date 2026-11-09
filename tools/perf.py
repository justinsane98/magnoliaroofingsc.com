#!/usr/bin/env python3
"""Page-weight pass: WebP copies of every referenced photo/logo + HTML rewrites.

    python3 -I tools/perf.py            # (build_pages.py also runs it after every build)

Visual output is meant to be identical; only bytes change:
  * every referenced .jpg/.png (>12 KB) gets a sibling .webp at the SAME pixel size
    (photos q80, alpha images q90). Originals stay for og:image / favicons / JSON-LD.
  * a few images are shown far smaller than they are stored, so they also get a
    downscaled variant that is still >= 3x the largest size CSS ever draws them at:
      X.logo.webp   marquee logos     (fit 450x192; CSS caps them at 150x64)
      X-card.webp   home router cards (1100 wide; cards are <= ~520 CSS px)
      X-thumb.webp  gallery strip     (1100 wide; slides are <= ~370 CSS px, ~735 on one-up tablets)
      site logo     .webp at 720 wide (header caps it at ~240 CSS px)
  * CSS: tools/purge_css.py writes trimmed copies of the GoSite stylesheets.
  * HTML: local image URLs point at the .webp; the Google Maps iframe lazy-loads;
    the RealWork Labs plugin loads after the page has loaded; the platform-JS
    preload hint is dropped (the script is at the end of <body> and was competing
    with the CSS and hero image for the first ~2 s).
Needs Pillow (with WebP) for the image step; the HTML step is plain Python.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_RE = re.compile(r"(/assets/[^\"'()\s?]+?)\.(jpg|jpeg|png)(\?v=\w+)?", re.I)
SITE_LOGO = "/assets/content.app-sources.com/s/683239219283733051/uploads/Images/08c954c5ab01b7cc2faafc73c7dd752fMagnoliaRoofingRemodelingLLC-1847027"
MIN_BYTES = 12 * 1024
SKIP = ("fav-", "/static.web-repository.com/")          # favicons, platform UI sprites


def fs(url):
    return os.path.join(ROOT, url.lstrip("/"))


def html_files():
    for d, _, files in os.walk(ROOT):
        if "/.git" in d or "/node_modules" in d:
            continue
        for f in files:
            if f.endswith(".html"):
                yield os.path.join(d, f)


def referenced():
    """Every local .jpg/.png URL the site points at (pages, scripts, data)."""
    urls = set()
    paths = list(html_files())
    for sub in ("assets/site", "tools"):
        for d, _, files in os.walk(os.path.join(ROOT, sub)):
            paths += [os.path.join(d, f) for f in files if f.endswith((".js", ".css", ".json", ".py"))]
    for p in paths:
        try:
            txt = open(p, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        for m in IMG_RE.finditer(txt):
            urls.add(m.group(1) + "." + m.group(2))
    # badge images are built from a pattern in hero.js
    for y in ("2025", "2026"):
        urls.add(f"/assets/site/badges/the-states-best-{y}.png")
    return sorted(u for u in urls if os.path.exists(fs(u)))


# ---------------------------------------------------------------- images
def make_images():
    from PIL import Image
    made = 0

    skip_file = os.path.join(ROOT, "tools", "perf-skip.json")
    skip = json.load(open(skip_file)) if os.path.exists(skip_file) else {}

    def save(src, dst, box=None, width=None):
        nonlocal made
        if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
            return
        if not (box or width) and skip.get(os.path.relpath(src, ROOT)) == os.path.getmtime(src):
            return
        im = Image.open(src)
        alpha = im.mode in ("RGBA", "LA", "P") and ("A" in im.getbands() or "transparency" in im.info)
        im = im.convert("RGBA" if alpha else "RGB")
        if box:
            im.thumbnail(box, Image.LANCZOS)                 # never upscales
        if width and im.width > width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        im.save(dst, "WEBP", quality=90 if alpha else 80, method=6)
        made += 1
        # same-size copies of grainy, high-detail photos barely shrink (2048px drone shots: -6%)
        # and would only cost quality; keep the original unless WebP saves at least a quarter
        if not (box or width) and os.path.getsize(dst) > 0.75 * os.path.getsize(src):
            os.remove(dst)
            skip[os.path.relpath(src, ROOT)] = os.path.getmtime(src)

    logos = {l["src"].split("?")[0] for l in json.load(open(os.path.join(ROOT, "tools", "logos.json")))}
    for url in referenced():
        src = fs(url)
        base = os.path.splitext(src)[0]
        if any(s in url for s in SKIP):
            continue
        if url in logos:
            save(src, base + ".logo.webp", box=(450, 192))
        if url.startswith(SITE_LOGO):
            save(src, base + ".webp", width=720)
            continue
        if "/assets/site/work/" in url:
            save(src, base + "-thumb.webp", width=1100)
        if re.search(r"/fb/(hero_[a-z_]+|flat_coated)\.jpg$", url):
            save(src, base + "-card.webp", width=1100)
        if os.path.getsize(src) >= MIN_BYTES or "/badges/" in url:
            save(src, base + ".webp")
    json.dump(skip, open(skip_file, "w"), indent=0, sort_keys=True)
    return made


# ---------------------------------------------------------------- html
KEEP_LINE = re.compile(r'og:image|itemprop="image"|twitter:image|rel="icon"|rel="apple-touch-icon"|"logo"\s*:|"image"\s*:')


def to_webp(m):
    path, ext, ver = m.group(1), m.group(2), m.group(3)
    if os.path.exists(fs(path + ".webp")):
        return path + ".webp"
    return m.group(0)


def rewrite_text(txt):
    out = []
    for line in txt.split("\n"):
        out.append(line if KEEP_LINE.search(line) else IMG_RE.sub(to_webp, line))
    return "\n".join(out)


RWL_OLD = re.compile(r"s\.parentNode\.insertBefore\(o, s\);")
RWL_NEW = ("(function(go){if(document.readyState==='complete')setTimeout(go,1500);"
           "else window.addEventListener('load',function(){setTimeout(go,1500)});})"
           "(function(){s.parentNode.insertBefore(o, s);}); /* mr:perf deferred */")


def rewrite_html(path):
    s = open(path, encoding="utf-8").read()
    t = rewrite_text(s)
    # platform JS: drop the head preload (the <script> itself stays where it is)
    t = re.sub(r'\s*<link rel="preload" as="script" href="/assets/static\.web-repository\.com/scripts/platform\.client\.min\.\w+\.js" />', "", t)
    # Google Fonts: the font CSS is render-blocking and the font files come from a second host; open both early
    if 'rel="preconnect" href="https://fonts.gstatic.com"' not in t and "fonts.googleapis.com/css" in t:
        t = re.sub(r'(<meta name="viewport"[^>]*>)', r'\1\n      <link rel="preconnect" href="https://fonts.googleapis.com">'
                   r'\n      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>', t, count=1)
    # Google Maps embed: below the fold everywhere it appears
    t = re.sub(r'<iframe(?![^>]*loading=)([^>]*src="https://www\.google\.com/maps/embed)',
               r'<iframe loading="lazy" title="Map: Magnolia Roofing office"\1', t)
    # site.js tags the first section .mr-hero after load; tag it in the HTML so its styles apply on first paint
    ci = t.find('<div class="content">')
    gi = t.find('class="grid-row', ci) if ci >= 0 else -1
    if gi >= 0 and "mr-hero" not in t[gi:gi + 60]:
        t = t[:gi] + 'class="grid-row mr-hero' + t[gi + len('class="grid-row'):]
    # RealWork Labs plugin (~290 KB JS): start it after the page has loaded
    if "mr:perf deferred" not in t:
        t = RWL_OLD.sub(RWL_NEW, t, count=1)
    if t != s:
        open(path, "w", encoding="utf-8").write(t)
        return True
    return False


def rewrite_assets():
    """work.json lists gallery photos; point it at the .webp copies."""
    p = os.path.join(ROOT, "assets", "site", "work.json")
    s = open(p, encoding="utf-8").read()
    t = rewrite_text(s)
    if t != s:
        open(p, "w", encoding="utf-8").write(t)


def main(images=True):
    n = 0
    if images:
        try:
            n = make_images()
        except ImportError:
            print("perf: Pillow not available, skipping image step", file=sys.stderr)
    rewrite_assets()
    changed = sum(rewrite_html(p) for p in html_files() if "/services/_shell.html" not in p)
    print(f"perf: {n} images written, {changed} pages rewritten")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import purge_css  # trimmed copies of the render-blocking GoSite stylesheets
    purge_css.main()


if __name__ == "__main__":
    main()
