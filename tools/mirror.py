#!/usr/bin/env python3
"""Mirror magnoliaroofssc.com (GoSite) into a static site for GitHub Pages.

Usage:  python3 -I tools/mirror.py            (run from repo root)

- Downloads each page + every asset on content.app-sources.com / static.web-repository.com
  (including url() refs inside CSS) into assets/, rewriting URLs to local paths.
- Strips GoSite-only hooks (messenger chat, gs analytics, platform hit tracker).
- Injects assets/site/site.js which replaces the GoSite form + chat with free services
  configured in assets/site/config.js.
Re-runnable: overwrites pages, re-downloads only missing assets.
"""
import gzip, hashlib, os, re, sys, urllib.parse, urllib.request

SRC = "https://magnoliaroofssc.com"
NEW = "https://magnoliaroofingsc.com"
PAGES = {"/": "index.html", "/services": "services/index.html"}
ASSET_HOSTS = ("content.app-sources.com", "static.web-repository.com")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
cache = {}

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    return gzip.decompress(data) if data[:2] == b"\x1f\x8b" else data

def local_path(url):
    p = urllib.parse.urlsplit(url)
    path = urllib.parse.unquote(p.path).lstrip("/") or "index"
    if p.query:  # keep variants distinct (?format=webp, ?v=1253) but stable
        base, ext = os.path.splitext(path)
        if not ext:
            ext = ".webp" if "webp" in p.query else ""
        path = f"{base}.{hashlib.md5(p.query.encode()).hexdigest()[:6]}{ext}"
    return f"assets/{p.netloc}/{path}"

def get_asset(url, depth=0):
    """Download an asset once; returns site-root-relative path ('/assets/...')."""
    url = url.replace("&amp;", "&")
    if url.startswith("//"):
        url = "https:" + url
    if url in cache:
        return cache[url]
    rel = local_path(url)
    dest = os.path.join(ROOT, rel)
    cache[url] = "/" + rel
    try:
        if os.path.exists(dest):
            return cache[url]  # already mirrored (CSS already rewritten) — don't rewrite twice
        data = fetch(url)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(data)
        if dest.endswith(".css") and depth < 3:
            css = open(dest, encoding="utf-8", errors="replace").read()
            def sub(m):
                ref = m.group(2).strip()
                if ref.startswith(("data:", "#")):
                    return m.group(0)
                return f"url({m.group(1)}{get_asset(urllib.parse.urljoin(url, ref), depth + 1)}{m.group(1)})"
            css = re.sub(r"url\((['\"]?)([^'\")]+)\1\)", sub, css)
            open(dest, "w", encoding="utf-8").write(css)
    except Exception as e:
        print(f"  ! {url}: {e}", file=sys.stderr)
        cache[url] = url  # leave remote on failure
    return cache[url]

ASSET_RE = re.compile(r"(?:https?:)?//(?:%s)/[^\s\"'()<>,]+" % "|".join(map(re.escape, ASSET_HOSTS)))

STRIP = [
    r'<script src="https://sitesjs\.gosite\.com/messenger/global-chat\.min\.js"[^>]*></script>',
    r'<script id="customAnalytics"[^>]*></script>',
    r'<script id="wb_id"[^>]*></script>',
    r'<script[^>]*src="[^"]*scripts/common/hit\.js[^"]*"[^>]*></script>',
    r'<script src="https://cdn\.userway\.org/widget\.js"[^>]*></script>',  # ADA overlay widget — not wanted
]

# Injected into <head>:
#  - GoSite's reCAPTCHA key is bound to their domains; FormSubmit/Web3Forms do their own spam filtering.
#  - "Powered by GoSite" footer badge — site is no longer on GoSite.
HEAD_CSS = ('<style>.recaptcha-target{display:none!important}'
            '.widget:has(a[href*="gosite.com"]){display:none!important}</style>\n')

def process(path, out):
    print(f"page {path} -> {out}")
    html = fetch(SRC + path).decode("utf-8")
    for pat in STRIP:
        html = re.sub(pat, "", html)
    html = ASSET_RE.sub(lambda m: get_asset(m.group(0)), html)
    # canonical/og URLs -> new domain; internal absolute links -> relative
    html = html.replace("https://magnoliaroofssc.com/", NEW + "/").replace('"https://magnoliaroofssc.com"', f'"{NEW}"')
    html = html.replace('href="//magnoliaroofssc.com"', 'href="/"').replace('href="/Home"', 'href="/"')
    html = html.replace("</head>", HEAD_CSS + "</head>", 1)
    hook = '<script src="/assets/site/config.js"></script>\n<script src="/assets/site/site.js"></script>\n'
    html = html.replace("</body>", hook + "</body>", 1)
    dest = os.path.join(ROOT, out)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w", encoding="utf-8").write(html)

if __name__ == "__main__":
    for p, o in PAGES.items():
        process(p, o)
    for f in ("robots.txt",):
        open(os.path.join(ROOT, f), "w").write(f"User-agent: *\nAllow: /\nSitemap: {NEW}/sitemap.xml\n")
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{NEW}{p}</loc></url>\n" for p in PAGES) + "</urlset>\n")
    print(f"done: {len(cache)} assets")
