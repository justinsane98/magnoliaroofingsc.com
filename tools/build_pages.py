#!/usr/bin/env python3
"""Build the audience pages, about page, case studies and service-area pages.

Uses services/index.html (the mirrored GoSite page) as the shell: its <head>, header,
hero row and footer are kept so every page looks like the rest of the site. Only the
content between the hero and the footer is replaced.

    python3 -I tools/build_pages.py

Content lives in tools/pages_content.py; town/county facts in tools/areas.json.
Anything Joe still has to supply is wrapped in <span class="fill">…</span> (yellow on the
page). Sample case studies carry a SAMPLE banner and are noindex until they're real.
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pages_content as C  # noqa: E402

SITE = "https://magnoliaroofingsc.com"
SHELL = os.path.join(ROOT, "services", "_shell.html")
import hashlib  # noqa: E402
PAGES_V = hashlib.md5(open(os.path.join(ROOT, "assets", "site", "pages.css"), "rb").read()).hexdigest()[:8]  # frozen copy of the original services page


def load_shell():
    if not os.path.exists(SHELL):
        src = open(os.path.join(ROOT, "services", "index.html"), encoding="utf-8").read()
        open(SHELL, "w", encoding="utf-8").write(src)
    return open(SHELL, encoding="utf-8").read()


NAV = [("/residential/", "Residential"), ("/commercial/", "Commercial"), ("/government/", "Government"),
       ("/real-estate/", "Real Estate"), ("/about/", "About")]


def nav_html(active):
    out = ['<ul class="clearfix">']
    for href, label in NAV:
        cls = "active " if href == active else " "
        out.append(f'<li class="{cls}"><a class="website-nav-link" rel="tab" href="{href}">{label}</a></li>')
    out.append("</ul>")
    return "".join(out)


def set_nav(page, active=None):
    """Replace every nav <ul> (desktop + mobile) that holds website-nav-link items."""
    def rep(m):
        return nav_html(active) if 'href="/#reviews"' in m.group(0) or 'href="/services"' in m.group(0) else m.group(0)
    return re.sub(r'<ul class="clearfix">[\s\S]*?</ul>', rep, page)


def split(shell):
    a = shell.index('<div class="content">\n') + len('<div class="content">\n')
    f = shell.index('  <footer class="page-footer')
    # first top-level row after `a` is the hero; find where it closes
    depth, i, hero_end = 0, a, None
    for m in re.finditer(r"<div\b|</div>", shell[a:f]):
        if m.group(0) == "</div>":
            depth -= 1
            if depth == 0:
                hero_end = a + m.end(); break
        else:
            depth += 1
    return shell[:a], shell[a:hero_end], shell[f:]


def esc(t):
    return html.escape(t, quote=True)


def page(path, title, desc, h1, body, hero_img=None, schema=None, noindex=False, active=None, sub=None):
    shell = load_shell()
    head, hero, foot = split(shell)
    url = SITE + path
    t, d = esc(title), esc(desc)
    head = re.sub(r"<title>.*?</title>", f"<title>{t}</title>", head, count=1)
    head = re.sub(r'(<link rel="canonical" href=")[^"]*', r"\g<1>" + url, head)
    head = re.sub(r'(<meta (?:property="og:url"|name="twitter:url") content=")[^"]*', r"\g<1>" + url, head)
    head = re.sub(r'(<meta (?:name="description"|property="og:description"|name="twitter:description") content=")[^"]*', lambda m: m.group(1) + d, head)
    head = re.sub(r'(<meta (?:property="og:title"|name="twitter:title") content=")[^"]*', lambda m: m.group(1) + t, head)
    ld = json.dumps(schema or C.business_schema(), indent=2, ensure_ascii=False)
    head = re.sub(r'<script type="application/ld\+json">[\s\S]*?</script>', lambda m: f'<script type="application/ld+json">\n{ld}\n</script>', head, count=1)
    if noindex:
        head = head.replace("</title>", '</title>\n      <meta name="robots" content="noindex, follow" />', 1)
    head = head.replace("</head>", f'<link rel="stylesheet" href="/assets/site/pages.css?v={PAGES_V}">\n</head>', 1)
    head = set_nav(head, active)
    # hero: new h1 (+ optional sub line) and background
    h = re.sub(r"(<h1[^>]*><span[^>]*>)[\s\S]*?(</span></h1>)", lambda m: m.group(1) + esc(h1) + m.group(2), hero, count=1)
    if sub:
        h = h.replace("</h1></div>", f'</h1><p style="text-align:center;line-height:1.4;margin-top:12px;"><span style="color:#fff;font-size:18px;">{esc(sub)}</span></p></div>', 1)
    if hero_img:
        h = re.sub(r"/assets/content\.app-sources\.com/s/\d+/uploads/Images/banner_Image-[^'\")]+", hero_img, h)
    content = f'<div class="grid-row mp" style="padding:0">{body}</div>\n'
    return head + h + content + "      </div>\n    </div>\n" + foot


def write(path, text):
    out = os.path.join(ROOT, path.strip("/"), "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(text)
    return out


def main():
    built = []
    for p in C.pages():
        built.append((p["path"], write(p["path"], page(**p))))
    # site-wide nav on the home page too
    home = os.path.join(ROOT, "index.html")
    s = open(home, encoding="utf-8").read()
    s2 = set_nav(s, None)
    s2 = re.sub(r'/assets/site/pages\.css(\?v=\w+)?"', f'/assets/site/pages.css?v={PAGES_V}"', s2)
    s2 = re.sub(r"<!-- mr:home-jobs -->[\s\S]*?<!-- /mr:home-jobs -->",
                lambda m: "<!-- mr:home-jobs -->\n" + C.home_jobs() + "\n<!-- /mr:home-jobs -->", s2, count=1)
    if s2 != s:
        open(home, "w", encoding="utf-8").write(s2)
    # preview: home page with the drone-motion hero (noindex, not in the sitemap)
    import hashlib as _h
    hm = os.path.join(ROOT, "assets", "site", "hero-motion.js")
    hv = _h.md5(open(hm, "rb").read()).hexdigest()[:8]
    # live home page gets the drone-motion hero too
    s3 = open(home, encoding="utf-8").read()
    s3 = re.sub(r'\s*<script src="/assets/site/hero-motion\.js[^"]*"></script>', "", s3)
    # hero: never show the old GoSite banner. Point data-parallax at a drone shot and pick the random
    # opening shot inline (before GoSite's parallax script reads the attribute) so there's no flash.
    s3 = re.sub(r'\n?<script id="mr-hero-pick">[\s\S]*?</script>', "", s3)
    ci = s3.index('<div class="content">')
    di = s3.index("data-parallax=\"", ci)
    de = s3.index('"', di + len('data-parallax="'))
    s3 = s3[:di] + 'data-parallax="/assets/site/hero-motion/shot-1.jpg' + s3[de:]
    te = s3.index(">", de) + 1
    # the inline style still painted GoSite's banner_Image for a moment before the shot replaced it: drop it and
    # set the background to the chosen (already preloaded) shot instead, so the first photo painted is the one that stays
    s3 = s3[:de] + re.sub(r"\s*background-image:\s*url\('[^']*banner_Image[^']*'\);?", "", s3[de:te], count=1) + s3[te:]
    te = s3.index(">", de) + 1
    pick = ('\n<script id="mr-hero-pick">(function(){var k=+document.documentElement.getAttribute("data-hero-shot")||0,e=document.currentScript.parentElement,'
            'u="/assets/site/hero-motion/shot-"+(k+1)+".jpg";e.setAttribute("data-parallax",u);e.style.backgroundImage="url(\'"+u+"\')";})();</script>')
    s3 = s3[:te] + pick + s3[te:]
    # the opening shot is the LCP image: choose it in <head> and preload it, so it is requested at once instead of
    # after the platform JS and hero-motion.js (it used to start ~3.7 s in on a slow phone). High priority: the
    # render-blocking CSS is small now (tools/purge_css.py) and is still requested first at "VeryHigh".
    s3 = re.sub(r'\n?\s*<script id="mr-hero-preload">[\s\S]*?</script>', "", s3)
    head_pick = ('\n      <script id="mr-hero-preload">(function(){var k=Math.floor(Math.random()*3),d=document,l=d.createElement("link");'
                 'd.documentElement.setAttribute("data-hero-shot",k);l.rel="preload";l.as="image";l.fetchPriority="high";'
                 'l.href="/assets/site/hero-motion/shot-"+(k+1)+".jpg";d.head.appendChild(l);})();</script>')
    vp = s3.index('<meta name="viewport"')
    vp = s3.index(">", vp) + 1
    s3 = s3[:vp] + head_pick + s3[vp:]
    # hero badges + classes in the HTML itself (hero.js used to add them after load and the headline jumped).
    # Wide screens: hero.js moves the badges into .grid-content (absolute, flanking the headline);
    # narrow: they sit in flow above the (hidden) eyebrow, which is where they are written here.
    s3 = re.sub(r'<div class="mr-badges"[^>]*>(?:<div class="mr-badge[^>]*><img[^>]*></div>)+</div><div class="mr-eyebrow" hidden></div>', "", s3)
    gi = s3.index('class="grid-row', ci)
    if "mr-hero--home" not in s3[gi:gi + 80]:
        s3 = s3[:gi] + 'class="grid-row mr-hero mr-hero--home' + s3[gi + len('class="grid-row'):]
    badges = ('<div class="mr-badges" aria-label="The State\'s Best roofer, winner 2025 and 2026">' + "".join(
        f'<div class="mr-badge mr-badge--{side}"><img src="/assets/site/badges/the-states-best-{y}.webp" '
        f'alt="The State\u2019s Best {y} Winner" width="144" height="142"></div>' for side, y in (("left", "2025"), ("right", "2026")))
        + '</div><div class="mr-eyebrow" hidden></div>')
    h1i = s3.index("<h1", ci)
    wr = s3.rindex('<div class="widget-row', 0, h1i)
    s3 = s3[:wr] + badges + s3[wr:]
    if "data-hero-motion" not in s3[:3000]:
        s3 = s3.replace("<html", "<html data-hero-motion", 1)
    s3 = s3.replace("</body>", f'<script src="/assets/site/hero-motion.js?v={hv}"></script>\n</body>', 1)
    s3 = re.sub(r'\s*<link rel="preload" as="image" href="/assets/site/hero-motion/shot-1\.jpg"[^>]*>', "", s3)
    # (no preload: the opening shot is random; hero-motion.js gives it fetchpriority=high)
    open(home, "w", encoding="utf-8").write(s3)
    pv = s3
    pv = re.sub(r"<title>.*?</title>", "<title>Hero motion preview | Magnolia Roofing</title>\n      <meta name=\"robots\" content=\"noindex, nofollow\" />", pv, count=1)
    pv_out = os.path.join(ROOT, "preview", "hero-motion", "index.html")
    os.makedirs(os.path.dirname(pv_out), exist_ok=True)
    open(pv_out, "w", encoding="utf-8").write(pv)
    # old town URLs redirect to their county page (not in the sitemap)
    for old, new, town in C.town_redirects():
        target = SITE + new
        stub = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{esc(town)} roofing | Magnolia Roofing</title>'
                f'<link rel="canonical" href="{target}"><meta name="robots" content="noindex, follow">'
                f'<meta http-equiv="refresh" content="0; url={new}"></head>'
                f'<body><p>{esc(town)} is covered on our <a href="{new}">county page</a>.</p></body></html>\n')
        write(old, stub)
    # sitemap: real pages only (samples are noindex)
    urls = ["/"] + [p["path"] for p in C.pages() if not p.get("noindex")]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"  <url><loc>{SITE}{u}</loc></url>" for u in urls]
    sm.append("</urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(sm) + "\n")
    import perf  # WebP image URLs, lazy map, deferred plugin (tools/perf.py)
    perf.main(images=False)
    for path, _ in built:
        print(path)
    print(len(built), "pages")


if __name__ == "__main__":
    main()
