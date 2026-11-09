#!/usr/bin/env python3
"""Font Awesome subsets: only the icons the site can actually show.

    python3 tools/subset_icons.py      (needs fontTools + brotli; perf.py runs it in the image step)

The GoSite CSS pulls in the full Font Awesome 6 fonts (~290 KB of woff2) for a
few dozen icons. For each font this writes X.subset.woff2 holding every icon
codepoint that any stylesheet rule, page or script can reference (glyph outlines
untouched, so icons render identically), plus X.subset.json listing those
codepoints. purge_css.py points the trimmed CSS at a subset only when its list
still covers everything needed, so adding an icon later can never show a blank
box - it just falls back to the full font until this is re-run.
"""
import glob, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FA_DIR = os.path.join(ROOT, "assets", "static.web-repository.com", "fonts", "fontawesome-v6")
PUA = (0xE000, 0xF8FF)


def in_pua(cp):
    return PUA[0] <= cp <= PUA[1]


def codepoints_in(text, kind):
    cps = set()
    if kind == "css":
        cps |= {int(h, 16) for h in re.findall(r"\\([0-9a-fA-F]{4,6})", text)}
    else:
        cps |= {int(h, 16) for h in re.findall(r"&#x([0-9a-fA-F]{4,6});", text)}
        cps |= {int(h) for h in re.findall(r"&#(\d{4,6});", text)}
        cps |= {int(h, 16) for h in re.findall(r"\\u([0-9a-fA-F]{4})", text)}
    cps |= {ord(c) for c in text if in_pua(ord(c))}
    return {c for c in cps if in_pua(c)}


def needed(extra_css=()):
    """Every private-use (icon) codepoint referenced by site CSS, pages and scripts."""
    cps = set()
    for css in extra_css:
        cps |= codepoints_in(css, "css")
    for d, _, files in os.walk(ROOT):
        if "/.git" in d or "/node_modules" in d or "/tools" in d:
            continue
        for f in files:
            p = os.path.join(d, f)
            if f.endswith(".css"):
                # the full GoSite originals are not served any more; their purged copies are passed in extra_css
                if re.search(r"/(platform\.client|trunk[-\d]*)\.min\.\w+\.css$", p):
                    continue
                cps |= codepoints_in(open(p, encoding="utf-8", errors="ignore").read(), "css")
            elif f.endswith((".html", ".js", ".json")):
                t = open(p, encoding="utf-8", errors="ignore").read()
                cps |= codepoints_in(t, "html")
                if f.endswith(".html"):
                    for st in re.findall(r"<style[^>]*>([\s\S]*?)</style>", t):
                        cps |= codepoints_in(st, "css")
                    for st in re.findall(r'style="([^"]*)"', t):
                        cps |= codepoints_in(st, "css")
    return cps


def main():
    from fontTools import subset
    from fontTools.ttLib import TTFont
    sys_path = os.path.dirname(os.path.abspath(__file__))
    import sys
    sys.path.insert(0, sys_path)
    import purge_css
    purged = [open(p, encoding="utf-8").read() for p in purge_css.purged_paths()]
    want = needed(purged)
    for src in sorted(glob.glob(os.path.join(FA_DIR, "*.woff2"))):
        if ".subset." in src:
            continue
        font = None
        for cand in (src, src[:-len(".woff2")] + ".ttf"):   # the woff2 browsers use; the .ttf if it's malformed
            try:
                font = TTFont(cand); font.ensureDecompiled(); break
            except Exception:
                font = None
        if font is None:
            print(f"icons: {os.path.basename(src)} unreadable; keeping the full font")
            continue
        have = set(font.getBestCmap())
        keep = sorted(want & have)
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        opts.glyph_names = True
        opts.hinting = True
        # keep the font-wide bounding box/metrics exactly as shipped: FA's declared box is smaller than its glyphs,
        # and "correcting" it changes how Chrome rasterises them (sub-pixel edge differences on ~40 icons)
        opts.recalc_bounds = False
        opts.recalc_max_context = False
        sub = subset.Subsetter(opts)
        sub.populate(unicodes=keep)
        keep_meta = {t: {k: getattr(font[t], k) for k in attrs} for t, attrs in (
            ("head", ("xMin", "yMin", "xMax", "yMax", "flags")),
            ("hhea", ("minLeftSideBearing", "minRightSideBearing", "xMaxExtent")))}
        sub.subset(font)
        for t, vals in keep_meta.items():
            for k, v in vals.items():
                setattr(font[t], k, v)
        base = src[:-len(".woff2")]
        from fontTools.ttLib.woff2 import WOFF2FlavorData
        font.flavor = "woff2"
        # no glyf/loca transform: it drops the per-glyph "overlapping contours" flag Font Awesome relies on,
        # which shifts anti-aliasing on icons with overlapping shapes (stars, chat bubbles...)
        font.flavorData = WOFF2FlavorData(transformedTables=())
        font.recalcBBoxes = False                    # see recalc_bounds above (save() would recompute them)
        font.save(base + ".subset.woff2")
        json.dump(sorted(want), open(base + ".subset.json", "w"))
        print(f"icons: {os.path.basename(src)} {os.path.getsize(src)//1024} KB -> "
              f"{os.path.getsize(base + '.subset.woff2')//1024} KB ({len(keep)} icons)")


if __name__ == "__main__":
    main()
