#!/usr/bin/env python3
"""Strip unused rules from the GoSite platform/theme stylesheets.

    python3 -I tools/purge_css.py      (perf.py runs it on every build)

The five GoSite stylesheets are render-blocking and ~900 KB raw, almost all of it
for widgets this site never uses. For each one we write a sibling
`<name>.p<hash>.css` and point every page at it; the originals are never edited,
so a re-run always purges from the full source.

Conservative by design - a rule is dropped only when one of its class/id names
appears NOWHERE in the site: not in any page, and not in any JavaScript (so
classes that scripts add later - open menus, lightbox, form errors, sliders -
are kept). Concretely, a selector is kept when every .class and #id it needs is
  * a word somewhere in the HTML/JS corpus, or
  * a string prefix the JS builds names from ("fa-" + icon) followed by a
    remainder that itself appears in the corpus (or is a number), or
  * contains characters we don't try to match (escaped names).
Classes inside :not()/:is()/:where()/:matches() don't count as required, element
and attribute selectors are always kept, and @font-face/@keyframes/@page and
every other at-rule body are kept verbatim; @keyframes are dropped only when
no kept rule and no page/script names them.
"""
import hashlib, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHEETS = [
    "assets/static.web-repository.com/styles/platform.client.min.d2e927.css",
    "assets/static.web-repository.com/t/theme28/css/trunk.min.d2e927.css",
    "assets/static.web-repository.com/t/theme28/css/trunk-1024.min.d2e927.css",
    "assets/static.web-repository.com/t/theme28/css/trunk-768.min.d2e927.css",
    "assets/static.web-repository.com/t/theme28/css/trunk-480.min.d2e927.css",
]
GROUPING = ("@media", "@supports", "@document", "@-moz-document", "@layer", "@container")


# ------------------------------------------------------------------ corpus
def corpus():
    words, prefixes = set(), set()
    for d, _, files in os.walk(ROOT):
        if "/.git" in d or "/node_modules" in d or "/tools" in d:
            continue
        for f in files:
            if not f.endswith((".html", ".js", ".json")):
                continue
            try:
                txt = open(os.path.join(d, f), encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            words.update(re.findall(r"[A-Za-z_][\w-]*", txt))
            if f.endswith((".js", ".html")):
                prefixes.update(re.findall(r"[\"'`]([A-Za-z_][\w-]*[-_])(?=[\"'`]|\$\{)", txt))
    return words, prefixes


# ------------------------------------------------------------------ parser
def split_blocks(css):
    """Top-level items: (prelude, body) for blocks, (stmt, None) for ; statements."""
    out, i, n, start = [], 0, len(css), 0
    while i < n:
        c = css[i]
        if c == "/" and css.startswith("/*", i):
            j = css.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if c in "\"'":
            i = skip_str(css, i)
            continue
        if c == ";":
            out.append((css[start:i + 1].strip(), None))
            start = i = i + 1
            continue
        if c == "{":
            depth, j = 1, i + 1
            while j < n and depth:
                cj = css[j]
                if cj in "\"'":
                    j = skip_str(css, j)
                    continue
                if cj == "/" and css.startswith("/*", j):
                    k = css.find("*/", j + 2)
                    j = n if k < 0 else k + 2
                    continue
                depth += cj == "{"
                depth -= cj == "}"
                j += 1
            out.append((css[start:i].strip(), css[i + 1:j - 1]))
            start = i = j
            continue
        i += 1
    tail = css[start:].strip()
    if tail:
        out.append((tail, None))
    return out


def skip_str(s, i):
    q, j = s[i], i + 1
    while j < len(s) and s[j] != q:
        j += 2 if s[j] == "\\" else 1
    return j + 1


# ------------------------------------------------------------------ matching
OPTIONAL_FN = re.compile(r":(?:not|is|where|matches|-webkit-any|-moz-any)\(")
NAME = re.compile(r"([.#])((?:\\.|[\w-])+)")


def strip_fn(sel):
    """Remove the arguments of :not()/:is()/... (their names are not required)."""
    while True:
        m = OPTIONAL_FN.search(sel)
        if not m:
            return sel
        i, depth = m.end(), 1
        while i < len(sel) and depth:
            depth += sel[i] == "("
            depth -= sel[i] == ")"
            i += 1
        sel = sel[:m.start()] + sel[i:]


def selector_used(sel, words, prefixes):
    s = re.sub(r"\[[^\]]*\]", "", strip_fn(sel))      # attribute selectors: keep
    s = re.sub(r"\"[^\"]*\"|'[^']*'", "", s)
    for kind, name in NAME.findall(s):
        if kind == "." and re.fullmatch(r"\d", name[:1]):  # e.g. 1.5em never reaches here, but be safe
            continue
        if "\\" in name:
            continue                                     # escaped names: don't guess
        if name in words or any(name.startswith(p) and built_ok(name[len(p):], words) for p in prefixes):
            continue
        return False
    return True


def built_ok(rest, words):
    """'fa-' + x: keep only if x itself shows up (an icon name, a number...)."""
    return rest == "" or rest.isdigit() or rest in words or re.fullmatch(r"\d+(?:-\d+)*", rest) is not None


KEYFRAMES = re.compile(r"@(?:-[a-z]+-)?keyframes\s+([\w-]+)", re.I)


def drop_unused_keyframes(css, words):
    """@keyframes nobody names: not in any kept animation declaration nor in the HTML/JS."""
    used = set(re.findall(r"[\w-]+", " ".join(re.findall(r"animation(?:-name)?\s*:([^;}]*)", css))))
    out = []
    for prelude, body in split_blocks(css):
        m = KEYFRAMES.match(prelude) if body is not None else None
        if m and m.group(1) not in used and m.group(1) not in words:
            continue
        if body is not None and prelude.lower().startswith(GROUPING):
            inner = drop_unused_keyframes(body, words)
            out.append(prelude + "{" + inner + "}" if inner else "")
            continue
        out.append(prelude if body is None else prelude + "{" + body + "}")
    return "".join(out)


def purge(css, words, prefixes, stats):
    out = []
    for prelude, body in split_blocks(css):
        if body is None:
            out.append(prelude if prelude.endswith(";") else prelude + ";")
            continue
        low = prelude.lower()
        if low.startswith("@"):
            if low.startswith(GROUPING):
                inner = purge(body, words, prefixes, stats)
                if inner:
                    out.append(prelude + "{" + inner + "}")
            else:
                out.append(prelude + "{" + body + "}")    # @font-face, @keyframes, @page...
            continue
        sels = split_selectors(prelude)
        keep = [s for s in sels if selector_used(s, words, prefixes)]
        stats["rules"] += 1
        if keep:
            out.append(",".join(keep) + "{" + body + "}")
        else:
            stats["dropped"] += 1
    return "".join(out)


def split_selectors(prelude):
    parts, depth, cur, i = [], 0, "", 0
    while i < len(prelude):
        c = prelude[i]
        if c in "\"'":
            j = skip_str(prelude, i)
            cur += prelude[i:j]
            i = j
            continue
        depth += c in "(["
        depth -= c in ")]"
        if c == "," and depth == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += c
        i += 1
    parts.append(cur.strip())
    return [p for p in parts if p]


# ------------------------------------------------------------------ driver
def html_files():
    for d, _, files in os.walk(ROOT):
        if "/.git" in d or "/node_modules" in d:
            continue
        for f in files:
            if f.endswith(".html"):
                yield os.path.join(d, f)


def main():
    words, prefixes = corpus()
    renames = {}
    for rel in SHEETS:
        src = os.path.join(ROOT, rel)
        css = open(src, encoding="utf-8").read()
        stats = {"rules": 0, "dropped": 0}
        out = drop_unused_keyframes(purge(css, words, prefixes, stats), words)
        h = hashlib.md5(out.encode()).hexdigest()[:8]
        base = rel[:-4]
        dst_rel = f"{base}.p{h}.css"
        for old in os.listdir(os.path.dirname(src)):           # drop stale purged copies
            full = os.path.join(os.path.dirname(src), old)
            if old.startswith(os.path.basename(base) + ".p") and old.endswith(".css") and full != os.path.join(ROOT, dst_rel):
                os.remove(full)
        open(os.path.join(ROOT, dst_rel), "w", encoding="utf-8").write(out)
        renames[base] = dst_rel
        print(f"purge: {os.path.basename(rel)} {len(css)//1024} KB -> {len(out)//1024} KB "
              f"({stats['dropped']}/{stats['rules']} rules dropped)")
    changed = 0
    for p in html_files():
        if "/services/_shell.html" in p:
            continue
        s = open(p, encoding="utf-8").read()
        t = s
        for base, dst in renames.items():
            t = re.sub(r"/" + re.escape(base) + r"(?:\.p[0-9a-f]{8})?\.css", "/" + dst, t)
        if t != s:
            open(p, "w", encoding="utf-8").write(t)
            changed += 1
    print(f"purge: {changed} pages repointed")


if __name__ == "__main__":
    main()
