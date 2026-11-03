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
    r'<script[^>]*id="rev-script"[^>]*></script>',  # GoSite review widget (hidden on live site) — replaced by reviews.js
]

# Copy fixes applied to the mirrored HTML (typos/grammar on the GoSite source).
COPY_FIXES = [
    (">Some of Our Works<", ">Some of Our Work<"),
    ("earn your trust-we'll", "earn your trust\u2014we'll"),
    ("roof problem-we have", "roof problem\u2014we have"),
    ("dedicated to you-we know", "dedicated to you\u2014we know"),
    ("roof repair services contact us today.", "roof repair services. Contact us today."),
    (">Servicing the following areas:", ">Serving the following areas:"),
    ("Saturday to Sunday: Closed", "Saturday and Sunday: Closed"),
    ("Put that Hammer In the Hands of a Pro", "Put That Hammer in the Hands of a Pro"),
    ("Excellence In What We Do", "Excellence in What We Do"),
    # "CALL US TODAY" buttons -> the phone number itself; clean dialable tel: link
    ("CALL US TODAY</span>", "(803) 908-7131</span>"),
    ('href="tel:(803) 908-7131"', 'href="tel:+18039087131"'),
]

REVIEWS_API = "https://webapi.gosite.com/api/reviewmanager/reviews/list?widget_id=we0O5pc1y5"

def refresh_reviews():
    """Snapshot all reviews from GoSite into assets/site/reviews.json (works only while the GoSite account exists)."""
    import json
    try:
        d = json.loads(fetch(REVIEWS_API))
    except Exception as e:
        print(f"  ! reviews not refreshed: {e}", file=sys.stderr)
        return
    out = [{"name": (r.get("authorName") or "").strip(), "rating": r.get("rating"),
            "date": (r.get("reviewDate") or "")[:10], "text": (r.get("content") or "").strip(),
            "source": r.get("siteId")} for r in d.get("reviews", [])]
    if not out:
        return
    out.sort(key=lambda r: r["date"], reverse=True)
    dest = os.path.join(ROOT, "assets/site/reviews.json")
    json.dump(out, open(dest, "w"), indent=1, ensure_ascii=False)
    print(f"reviews: {len(out)}")

HEAD_CSS = '<link rel="stylesheet" href="/assets/site/site.css">\n'  # overrides: see assets/site/site.css

def process(path, out):
    print(f"page {path} -> {out}")
    html = fetch(SRC + path).decode("utf-8")
    for pat in STRIP:
        html = re.sub(pat, "", html)
    html = ASSET_RE.sub(lambda m: get_asset(m.group(0)), html)
    # canonical/og URLs -> new domain; internal absolute links -> relative
    html = html.replace("https://magnoliaroofssc.com/", NEW + "/").replace('"https://magnoliaroofssc.com"', f'"{NEW}"')
    html = html.replace('href="//magnoliaroofssc.com"', 'href="/"').replace('href="/Home"', 'href="/"')
    for a, b in COPY_FIXES:
        html = html.replace(a, b)
    html = html.replace("</head>", HEAD_CSS + "</head>", 1)
    hook = '<script src="/assets/site/config.js"></script>\n<script src="/assets/site/site.js"></script>\n<script src="/assets/site/scrubber.js"></script>\n<script src="/assets/site/reviews.js"></script>\n<script src="/assets/site/gallery.js"></script>\n'
    html = html.replace("</body>", hook + "</body>", 1)
    dest = os.path.join(ROOT, out)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w", encoding="utf-8").write(html)

if __name__ == "__main__":
    for p, o in PAGES.items():
        process(p, o)
    refresh_reviews()
    for f in ("robots.txt",):
        open(os.path.join(ROOT, f), "w").write(f"User-agent: *\nAllow: /\nSitemap: {NEW}/sitemap.xml\n")
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{NEW}{p}</loc></url>\n" for p in PAGES) + "</urlset>\n")
    print(f"done: {len(cache)} assets")
