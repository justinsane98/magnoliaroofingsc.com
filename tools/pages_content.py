"""Copy for the generated pages. Edit here, then run: python3 -I tools/build_pages.py

F("…") marks a blank Joe still has to fill (shows yellow on the page; search the HTML for class="fill").
Reviews quoted below are real Google/Facebook reviews from assets/site/reviews.json.
"""
import html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PHONE, TEL = "(803) 908-7131", "tel:+18039087131"
PHOTOS = json.load(open(os.path.join(HERE, "photos.json")))   # key -> {src, alt}
AREAS = json.load(open(os.path.join(HERE, "areas.json")))["places"]


HEDGE = r'\s*\((?:part|parts|most|mostly|partial|partly|portion)[^)]*\)'  # '(part)', '(most)' etc. are never shown


def and_list(items):
    """'A, B and C' (house style: full lists, no serial comma, no '(part)' hedges)."""
    items = [re.sub(HEDGE, "", str(x)).strip() for x in items if str(x).strip()]
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def county_link(c):
    """Linked county name; accepts 'Aiken' or 'Aiken County'."""
    n = c if c.endswith(" County") else c + " County"
    return f'<a href="/service-areas/{slug(n)}/">{n}</a>'


def counties_by_tier(tier=None):
    cov = json.load(open(os.path.join(HERE, "coverage.json")))["counties"]
    return sorted(k for k, v in cov.items() if tier is None or v["tier"] == tier)


def F(t):
    return f'<span class="fill" title="Joe to fill in">{t}</span>'


def img(key, cls="pic", alt=None):
    p = PHOTOS[key]
    return f'<img class="{cls}" src="{p["src"]}" alt="{alt or p["alt"]}" loading="lazy">'


def img_size(path):
    """(w, h) of a PNG, JPEG, WebP or SVG without Pillow (the build runs on plain python3)."""
    import struct
    b = open(path, "rb").read(65536)
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", b[16:24])
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        c = b[12:16]
        if c == b"VP8X":
            return (int.from_bytes(b[24:27], "little") + 1, int.from_bytes(b[27:30], "little") + 1)
        if c == b"VP8L":
            v = int.from_bytes(b[21:25], "little")
            return ((v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1)
        if c == b"VP8 ":
            w, h = struct.unpack("<HH", b[26:30])
            return (w & 0x3FFF, h & 0x3FFF)
    if b[:2] == b"\xff\xd8":
        i = 2
        while i < len(b) - 9:
            if b[i] != 0xFF:
                i += 1
                continue
            m = b[i + 1]
            if m in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", b[i + 5:i + 9])
                return (w, h)
            i += 2 + struct.unpack(">H", b[i + 2:i + 4])[0]
    m = re.search(rb'<svg[^>]*?\bwidth="([\d.]+)"[^>]*?\bheight="([\d.]+)"', b)
    if m:
        return (round(float(m.group(1))), round(float(m.group(2))))
    return None


def card_img(key):
    """Router-card photo: the 1100px copy from tools/perf.py when it exists (cards are <= ~520 CSS px)."""
    src = PHOTOS[key]["src"]
    card = os.path.splitext(src)[0] + "-card.webp"
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.exists(os.path.join(root, card.lstrip("/"))):
        src = card
    return f'<img class="" src="{src}" alt="" loading="lazy">'


def ba(before, after):
    return (f'<div class="ba"><figure>{img(before, "")}<figcaption>Before</figcaption></figure>'
            f'<figure>{img(after, "")}<figcaption>After</figcaption></figure></div>')


def photos(keys):
    return '<div class="photos">' + "".join(f'<figure>{img(k, "")}</figure>' for k in keys) + "</div>"


def ticks(items):
    return '<ul class="ticks">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def cards(items, cls="grid"):
    out = [f'<div class="{cls}">']
    for it in items:
        tag, attrs = ("a", f' href="{it["href"]}"') if it.get("href") else ("div", "")
        pic = img(it["img"], "") if it.get("img") else ""
        sym = f'<span class="sym">{it["sym"]}</span>' if it.get("sym") else ""
        more = f'<p class="more">{it.get("more", "Learn more")} →</p>' if it.get("href") else ""
        out.append(f'<{tag} class="card"{attrs}>{pic}{sym}<h3>{it["h"]}</h3><p>{it["p"]}</p>{more}</{tag}>')
    out.append("</div>")
    return "".join(out)


def steps(items):
    return '<div class="steps">' + "".join(f"<div><h3>{h}</h3><p>{p}</p></div>" for h, p in items) + "</div>"


AREA_Q = re.compile(r"\b(areas?|where do you (work|bid)|cover)\b", re.I)


def faq(items):
    """House rule: the service-area question always comes first."""
    items = sorted(items, key=lambda qa: 0 if AREA_Q.search(qa[0]) else 1)  # stable: others keep their order
    return "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in items)


def quote(text, who, note=""):
    n = f" <small>· {note}</small>" if note else ""
    return f"<blockquote><p>“{text}”</p><cite>{who}{n}</cite></blockquote>"


def sec(inner, cls="", wrap=True):
    c = f' class="{cls}"' if cls else ""
    return f"<section{c}>" + (f'<div class="wrap">{inner}</div>' if wrap else inner) + "</section>"


def head(eyebrow, h2, lede=""):
    return (f'<span class="eyebrow">{eyebrow}</span>' if eyebrow else "") + f"<h2>{h2}</h2>" + (f'<p class="lede">{lede}</p>' if lede else "")


def promo(eyebrow, h2, lede, href, label, photo):
    """Green feature card that points to another audience page."""
    return (f'<div class="promo"><div class="promo-text">{head(eyebrow, h2, lede)}'
            f'<p><a href="{href}" class="theme-button hvr-grow-shadow mr-btn-pri">{label.upper()}</a></p></div>'
            f'<div class="promo-pic">{img(photo)}</div></div>')


MSG = ('<a href="#chat" data-chat="true" class="theme-button hvr-grow-shadow gs-chat-btn mr-chat-secondary mr-btn-sec">'
       '<span class="mr-msg-long">SEND A MESSAGE</span><span class="mr-msg-short">MESSAGE</span></a>')
CALL = f'<a href="{TEL}" class="theme-button hvr-grow-shadow mr-phone-cta mr-btn-pri">{PHONE}</a>'
BTNS = f'<div class="btns">{MSG}{CALL}</div>'   # secondary left, primary right (also on phones)


def link_btn(href, label):
    return f'<a href="{href}" class="theme-button hvr-grow-shadow mr-btn-pri">{label.upper()}</a>'


def cta(h="Talk to a roofer, not a call center", p="Joe or someone on his team picks up. Free inspections with photos."):
    return sec(f'<div class="cta-band"><div><h2>{h}</h2><p>{p}</p></div>{BTNS}</div>')


def business_schema(extra=None):
    s = {
        "@context": "https://schema.org", "@type": "RoofingContractor",
        "name": "Magnolia Roofing & Remodeling LLC", "url": "https://magnoliaroofingsc.com/",
        "telephone": "+1-803-908-7131", "email": "magnoliaroofingsc@gmail.com",
        "address": {"@type": "PostalAddress", "streetAddress": "6236 St Andrews Rd #9", "addressLocality": "Columbia",
                    "addressRegion": "SC", "postalCode": "29212", "addressCountry": "US"},
        "areaServed": [{"@type": "State", "name": "South Carolina"}] + [a["name"] + (", SC" if a["type"] == "town" else ", SC") for a in AREAS],
        "foundingDate": "2018", "founder": {"@type": "Person", "name": "Joe Nettles"},
        "sameAs": ["https://www.facebook.com/magnoliaroofingsc/"],
    }
    if extra:
        s.update(extra)
    return s


# ------------------------------------------------------------------ case studies (SAMPLES)
SAMPLE_NOTE = ('<div class="sample"><span class="sample-tag">SAMPLE</span><br><b>This is a made-up example to show the format.</b> '
               'Every yellow blank needs a real job, real numbers and real photos before this page goes live. '
               'It is hidden from Google (noindex) until then.</div>')

CASES = [
    {
        "slug": "office-flat-roof-restoration", "hero": "hero_case_office", "kind": "Commercial", "for": "/commercial/",
        "title": "Two-story office, St. Andrews: stopping chronic flat-roof leaks without closing the building",
        "short": "Restore, repair or replace? How we priced all three for a leaking low-slope office roof and why the owner chose restoration.",
        "img": "flat_coated",
        "stats": [("Roof size", F("14,000 sq ft")), ("System", F("silicone restoration over existing modified bitumen")),
                  ("On site", F("6 working days")), ("Building open", "Every day"), ("Warranty", F("10-year manufacturer"))],
        "body": [
            ("The building", f"A {F('1980s')} two-story office off St. Andrews Road with {F('9')} tenants. Low-slope modified bitumen roof, "
             f"{F('about 22')} years old, with ponding at two drains and {F('6')} active leaks over the winter."),
            ("What the owner needed to decide", "Patch it again, restore it, or tear it off? The property manager needed numbers for the owner and "
             "a plan that didn't send tenants home."),
            ("What we found", f"Core cuts showed the insulation was dry over {F('85%')} of the roof. Wet areas were mapped with {F('infrared scan / moisture meter')} "
             "and marked on a photo plan. That one fact decided the job: dry insulation means the roof can be restored instead of replaced."),
        ],
        "options": [("Keep patching", F("$4–6k a year"), "Cheapest this year, but leaks return and the roof keeps aging."),
                    ("Restore (chosen)", F("$X per sq ft"), "Replace wet sections, rebuild drains, coat. About a third of replacement cost and qualifies for a manufacturer warranty."),
                    ("Full replacement", F("$X per sq ft"), "Right answer when the deck or insulation is shot. It wasn't here.")],
        "did": [f"Cut out and replaced {F('1,900 sq ft')} of wet insulation and membrane",
                "Rebuilt both drains with new sumps and clamping rings to fix ponding",
                "Reinforced seams, flashings and penetrations, then applied the coating system",
                "Worked early mornings for the noisy work; tenants got a schedule a week ahead",
                "Photo report and warranty paperwork to the owner at closeout"],
        "result": f"No leaks through {F('two hurricane seasons')}. Owner paid {F('about 35%')} of the replacement quote and added {F('10–15 years')} of service life.",
        "ask": ["Has anyone actually checked whether the insulation is wet?", "Does the restoration carry a manufacturer warranty, or just the contractor's?",
                "How will you keep tenants working during the noisy parts?", "Will I get a photo report I can give my owner or insurer?"],
        "quote": None,
    },
    {
        "slug": "county-maintenance-building-reroof", "hero": "hero_case_county", "kind": "Government", "for": "/government/",
        "title": "County maintenance building: an IFB reroof delivered on schedule with full closeout paperwork",
        "short": "What it takes to win and finish a public roofing bid: pre-bid, bonds, submittals, prevailing wage and a clean closeout.",
        "img": "crew_tearoff",
        "stats": [("Contract", F("$000,000")), ("Delivery", F("IFB, low bid")), ("Roof", F("standing seam metal, 9,600 sq ft")),
                  ("Schedule", F("45 days, finished in 38")), ("Change orders", F("1, for rotted decking at unit price"))],
        "body": [
            ("The solicitation", f"{F('[County]')} posted an Invitation for Bid for a tear-off and new roof on a vehicle maintenance building. "
             f"Mandatory pre-bid on {F('[date]')}, bid bond required, performance and payment bonds on award."),
            ("Before we priced it", "We attended the pre-bid, walked the roof, and asked one question in writing: how much rotted decking to carry. "
             "The answer came back as an addendum with a unit price line, which kept every bidder on the same footing."),
            ("Submittals", "Product data, shop drawings for the trim, manufacturer installer letter, warranty sample, safety plan and the schedule. "
             f"Approved in {F('one round')}."),
        ],
        "options": None,
        "did": ["Phased tear-off so bays stayed usable and nothing was left open overnight",
                f"Replaced {F('640 sq ft')} of decking at the bid unit price, documented with photos and logged daily",
                "Daily logs and photos to the county project manager",
                f"{F('Certified payroll / prevailing wage')} where the funding required it",
                "Closeout binder: as-builts, warranties, lien waivers, O&M data and the final photo set"],
        "result": f"Finished {F('7 days')} early with {F('no')} punch-list items left open and {F('no')} claims. The county added us to their {F('on-call roof repair list')}.",
        "ask": ["Will they come to the pre-bid and walk the roof?", "How do they price unknowns like rotten decking?",
                "Can they bond the job and show the bonding letter up front?", "Do they deliver a complete closeout binder, or just an invoice?"],
        "quote": None,
    },
    {
        "slug": "inspection-repairs-before-closing", "hero": "hero_case_closing", "kind": "Real estate", "for": "/real-estate/",
        "title": "Seven days to closing: fixing a buyer's inspection list and handing the agent a roof letter",
        "short": "How a listing agent kept a closing on schedule: same-week inspection, repairs and a written roof condition letter for the buyer's side.",
        "img": "flashing_new",
        "stats": [("Days to closing", F("7")), ("Items on the report", F("5 roof, 1 siding")), ("Repaired in", F("2 days")),
                  ("Letter delivered", F("Day 3")), ("Closing", "On time")],
        "body": [
            ("The call", f"A listing agent in {F('[Lexington]')} sent the buyer's inspection report on a {F('Monday')}: lifted shingles, exposed nails, "
             "a failed boot on a plumbing vent, loose chimney flashing and damaged J-trim. Closing was the next week."),
            ("Same day", "We looked the same afternoon, photographed every item against the inspector's list, and sent a fixed price for each one "
             "so the seller could decide line by line."),
            ("What the buyer's agent needed", "Not just 'fixed'. They wanted proof. So the report shows each inspection item, the before photo, the after photo and what was done."),
        ],
        "options": None,
        "did": ["Resealed and replaced lifted shingles, fixed exposed nails",
                "Replaced the pipe boot and reflashed the chimney with new counter-flashing",
                "Replaced the damaged J-trim and siding pieces to match",
                f"Wrote a roof condition letter covering {F('remaining life estimate and workmanship warranty')}",
                "Sent one PDF to both agents: inspection item → photo → fix"],
        "result": "The repair addendum was signed off the same day the PDF arrived and closing happened on schedule.",
        "ask": ["Can you get out this week, not in three weeks?", "Will you price each inspection item separately?",
                "Will I get before and after photos keyed to the inspection report?", "Will you put the roof's condition in writing?"],
        "quote": ("Was selling my home and after inspection I was required to repair my J trim/siding on my home. Only a week left till closing on my property, this repair needed to be done ASAP.",
                  "Anne Morrow", "real review, Apr 2026"),
    },
]


def case_card(c):
    return {"href": f"/case-studies/{c['slug']}/", "img": c["img"], "sym": f"SAMPLE · {c['kind']}", "h": c["title"], "p": c["short"], "more": "Read the case study"}


def case_page(c):
    stats = '<div class="stats">' + "".join(f"<div><b>{v}</b><span>{k}</span></div>" for k, v in c["stats"]) + "</div>"
    parts = [sec(SAMPLE_NOTE + f'<span class="eyebrow">{c["kind"]} case study</span><h2>{c["title"]}</h2><p class="lede">{c["short"]}</p>{stats}'
                 f'<div class="split"><div>' + "".join(f"<h3>{h}</h3><p>{p}</p>" for h, p in c["body"]) + f"</div><div>{img(c['img'])}</div></div>")]
    if c["options"]:
        rows = "".join(f'<div class="card"><span class="sym">{cost}</span><h3>{name}</h3><p>{why}</p></div>' for name, cost, why in c["options"])
        parts.append(sec(head("The decision", "Three options, priced side by side", "This is the comparison the owner saw. Most roofers only quote the one they want to sell.") + f'<div class="grid">{rows}</div>', "tint"))
    parts.append(sec(f'<div class="split"><div>{head("", "What we did")}{ticks(c["did"])}<h3>Result</h3><p>{c["result"]}</p></div>'
                     f'<div class="card"><h3>Questions to ask any roofer on a job like this</h3>{ticks(c["ask"])}</div></div>'))
    if c["quote"]:
        parts.append(sec(quote(*c["quote"]), "tint"))
    parts.append(sec(head("", "Photos from this job") + f'<p>{F("Before, during and after photos from the real job go here.")}</p>' + photos(["placeholder_1", "placeholder_2", "placeholder_3"])))
    parts.append(cta())
    return {"path": f"/case-studies/{c['slug']}/", "title": f"{c['title']} | Magnolia Roofing case study",
            "desc": c["short"], "h1": f"{c['kind']} case study", "body": "".join(parts), "noindex": True, "hero_img": PHOTOS[c["hero"]]["src"]}


# ------------------------------------------------------------------ reviews we quote (real)
R = {
    "akers": ("Not only did they replace my roof, they took care of my ceiling that was destroyed by water seeping through missing shingles.", "Johanita Akers", "Google review"),
    "king": ("Most recently they were able to quickly identify a tiny roof leak and get it fixed.", "Lauren King", "Google review"),
    "michael": ("Magnolia replaced our entire roof due to some damage from wind as well as its overall age… especially dealing with the insurance company.", "Michael S", "Google review"),
    "john": ("I've been a carpenter for over 50 years and done many roofs… I was truly impressed with the entire experience.", "John", "insurance claim, Google review"),
    "adams": ("We interviewed around 6 roofing companies. We went with Magnolia. They were relaxed, honest… and didn't try to upsell.", "Kris Adams", "Google review"),
    "cc": ("We had Magnolia handle a roof replacement at our office last year… Price was reasonable, work completed in a timely manner.", "CC", "office roof replacement, Google review"),
    "drawdy": ("They completed the job on time as promised, and cleaned up the mess.", "Lehe Drawdy", "office repair, Google review"),
    "kim": ("My real estate team has been using and referring this company for over 5 years.", "Tricia Kim", "real estate team"),
    "hemphill": ("As a Realtor in Columbia, Joe is always my first call whenever I need a roof inspection done or one of my clients has a roofing concern.", "LaCretia Hemphill", "Realtor"),
    "royall": ("As a Realtor of 15 years, I've seen many a shady contractor… [Magnolia is] my trustworthy go-to.", "Renee Bumgarner Royall", "Realtor"),
    "polinsky": ("I have personally utilized Magnolia Roofing and Remodeling for my personal home and a number of homes I have listed and sold.", "Felicia Polinsky", "Realtor"),
    "ryan": ("They work well with insurance adjusters to help ensure damaged roofs are taken care of.", "Bev Ryan", "Realtor"),
    "horton": ("Our closing day was quickly approaching and we needed the fixes done asap for our buyers.", "Gina Horton", "home seller"),
    "pound": ("Joe and his team inspected our old home for our new buyers AND our new home!", "Breanna Pound", "seller and buyer"),
    "duque": ("We use them for real estate repairs and our customers always love their work.", "Evelio Duque", "real estate"),
    "williams": ("He partners with me on every roofing inspection for my clients.", "Velecia Lynette Williams", "Realtor"),
    "romlein": ("Most distinctive and appreciated was the personal follow up from the owners to inspect the quality.", "Jason Romlein", "Google review"),
}


def quotes(keys):
    return '<div class="grid two">' + "".join(quote(*R[k]) for k in keys) + "</div>"


# ------------------------------------------------------------------ pages
def residential():
    problems = [
        {"sym": "Leaks", "h": "Water stain on the ceiling", "p": "Most leaks start at flashing, pipe boots or chimneys, not the field of the roof. We find the actual entry point and fix that, then tell you honestly if the roof has more life in it.", "img": "chimney_flash"},
        {"sym": "Storm damage", "h": "Shingles blew off or a tree came down", "p": "Same-day tarping when we can, photos for your insurance company, and we meet the adjuster on the roof so nothing gets missed.", "img": "tree_damage"},
        {"sym": "Insurance", "h": "Hail or wind claim", "p": "We document the damage, walk the roof with your adjuster and handle the paperwork. You pay your deductible, nothing more.", "img": "storm_marked"},
        {"sym": "Old roof", "h": "Repair or replace?", "p": "A 15-year-old roof with one bad spot needs a repair, not a sales pitch. We show you photos and give you both prices when both make sense.", "img": "worn_shingles"},
        {"sym": "Rot", "h": "Soft spots and sagging", "p": "Soft decking means water has been getting in for a while. We replace rotten wood at a price per sheet agreed before we start, so there are no surprises.", "img": "rot_deck"},
        {"sym": "Exterior", "h": "Siding, trim and gutters", "p": "Storm-torn siding, rotted trim and overflowing gutters cause the same water damage as a bad roof. We fix those too.", "img": "siding"},
    ]
    body = [
        sec(head("Homeowners in the Midlands &amp; Lowcountry", "What's going on with your roof?",
                 "Start with the problem. We'll tell you what it is, what it costs to fix, and whether you need a roofer at all. Sometimes it's the AC line, and we'll say so.") + cards(problems)),
        sec(f'<div class="split"><div>{head("Our process", "Free inspection, real photos, straight answers")}'
            + ticks(["We get on the roof (or fly a drone) and photograph everything we find",
                     "You get the photos and a plain-English explanation, not a high-pressure close",
                     "Repair price and replacement price when both make sense",
                     "Install day: tarps over landscaping, magnetic sweep for nails, daily cleanup",
                     "Joe or a lead does a final walk with you before we call it done"])
            + f'</div><div>{ba("house_before", "house_after")}</div></div>', "tint"),
        sec(head("Roof replacement", "Shingle and metal roofs, installed right the first time",
                 f"Architectural shingles from {F('IKO / GAF / Owens Corning / CertainTeed: confirm which lines Joe installs and which certifications are current')}, and metal roofing. "
                 "Every replacement includes new underlayment, ice and water shield in valleys and at penetrations, new pipe boots and flashing, and ridge ventilation sized for your attic.")
            + steps([("Tear-off", "Down to the decking so we can see and replace any rot."),
                     ("Dry-in", "Synthetic underlayment and ice and water shield the same day."),
                     ("Install", "Starter, shingles, flashing, boots and ridge vents to manufacturer spec."),
                     ("Clean up", "Magnet sweep, haul-off and a final walk with you.")])
            + f'<p style="margin-top:18px">Warranty: {F("manufacturer warranty level and Magnolia workmanship years")}. Most homes are done in {F("1–2 days")}.</p>'),
        sec(head("What our neighbors say", "Real reviews from Midlands homeowners") + quotes(["akers", "king", "michael", "adams"]), "tint"),
        sec(promo("Selling or buying?", "Inspection repairs on a deadline",
                  "Realtors send us their inspection reports. See how we handle repairs before closing.",
                  "/real-estate/", "Real estate &amp; property managers", "hero_real_estate")),
        sec(head("", "Common questions") + faq([
            ("How do I know if I need a repair or a new roof?", "Age, how many problem spots there are, and whether the decking is soft. We'll show you photos of each and give you both prices if both make sense."),
            ("Will insurance pay for my roof?", "If wind or hail damaged it, often yes. If it's worn out from age, no. We'll tell you which one it looks like before you file, so you don't take a claim you don't need."),
            ("How long does a replacement take?", f"Most homes take {F('1–2 days')}. Bigger or steeper roofs take longer, and we'll tell you up front."),
            ("Do you offer financing?", F("Yes / no, and who the financing partner is")),
            ("What areas do you serve?", "Homes in " + and_list(county_link(c) for c in counties_by_tier("core")) + ". Commercial, government and real estate work in every county: <a href=\"/service-areas/\">see the coverage map</a>."),
        ])),
        cta(),
    ]
    return {"path": "/residential/", "active": "/residential/", "title": "Residential Roofing in the Midlands & Lowcountry, SC: Roof Repair, Replacement & Storm Damage | Magnolia Roofing",
            "desc": "Roof leaks, storm and hail damage, insurance claims and roof replacement for homeowners in the Midlands and Lowcountry. Free inspections with photos. Call (803) 908-7131.",
            "h1": "Residential roofing", "sub": "Leaks, storm damage, insurance claims and new roofs, with photos and straight answers.",
            "hero_img": PHOTOS["hero_residential"]["src"], "body": "".join(body)}


def commercial():
    who = [
        {"sym": "Offices & medical", "h": "Office and medical buildings", "p": "Leak repairs scheduled around tenants and patients, with photo reports for owners and property managers."},
        {"sym": "Churches", "h": "Churches and fellowship halls", "p": "Big roofs, small budgets and committees. We price options so the building committee can choose, and we work around services."},
        {"sym": "Retail & restaurants", "h": "Retail strips and restaurants", "p": "Rooftop units, grease, ponding and lots of penetrations. We keep the doors open while we work."},
        {"sym": "Industrial", "h": "Warehouses and shops", "p": "Metal roof repair and retrofit, fastener and seam work, skylights and gutters."},
        {"sym": "Multifamily", "h": "Apartments and HOAs", "p": "Phased replacement across buildings, one point of contact, resident notices and a schedule you can share."},
        {"sym": "General contractors", "h": "Roofing subcontractor for GCs", "p": f"Insured, {F('bonded')}, and on time for your schedule. We price from your plans and specs."},
    ]
    systems = [
        {"h": "Low-slope / flat roofs", "p": f"{F('TPO, modified bitumen, EPDM: confirm which systems Magnolia installs')}. Repair, recover or full replacement."},
        {"h": "Roof restoration & coatings", "p": f"Silicone or acrylic restoration over a sound roof. Often a fraction of replacement cost and eligible for a manufacturer warranty when the insulation is dry. {F('confirm coating brand')}"},
        {"h": "Metal roofs", "p": "Standing seam and exposed-fastener metal: new, repair, re-screw and seam sealing."},
        {"h": "Steep-slope commercial", "p": "Architectural shingles on churches, offices and apartment buildings."},
        {"h": "Maintenance plans", "p": f"Twice-a-year inspections, drain cleaning and minor repairs with a photo report after every visit. {F('price per sq ft or flat fee')}"},
        {"h": "Emergency leak response", "p": f"Call {PHONE}. {F('Response time commitment, e.g. on site within 24 hours')}"},
    ]
    body = [
        sec(head("For owners, facility and property managers", "Commercial roofing that keeps the building open",
                 "We work on occupied buildings across South Carolina. You get an inspection with photos, options priced side by side, a schedule your tenants can live with, and a closeout report you can hand to an owner, a board or an insurer.")
            + cards(who)),
        sec(f'<div class="split"><div>{head("Systems", "What we install and repair", "Flat, low-slope, metal and steep-slope roofs on occupied buildings. We tell you whether a roof needs a repair, a restoration coating or a full replacement, and price the options side by side so you can choose.")}</div><div>{img("flat_coated")}</div></div>' + cards(systems), "tint"),
        sec(head("Case studies", "How we approach commercial jobs", "These examples show the level of detail you'll get from us. Real project write-ups are coming.") + cards([case_card(CASES[0]), case_card(CASES[1])], "grid two")),
        sec(head("How a commercial job runs", "No surprises from first call to closeout") + steps([
            ("Assessment", f"Roof walk, core cuts where needed, {F('moisture scan')} and a photo plan of every problem."),
            ("Options", "Repair, restore or replace, each priced, with the life you can expect from each."),
            ("Schedule", "Noisy work early, staging away from entrances, notices for tenants a week ahead."),
            ("Closeout", "Photo report, warranty paperwork and a maintenance recommendation."),
        ])),
        sec(head("What business owners say", "") + quotes(["cc", "drawdy"]), "tint"),
        sec(head("Credentials", "Ready for your vendor file") + ticks([
            f"SC contractor license: {F('license number and classification')}",
            f"General liability {F('$ limits')} and workers' comp. Certificate of insurance on request, same day",
            f"Bonding capacity: {F('single job / aggregate')}",
            f"Manufacturer certifications: {F('list')}",
            "The State's Best roofer, 2025 and 2026 (The State newspaper readers' choice)",
        ]) + '<p>Public agency? See <a href="/government/">municipal and government roofing</a>.</p>'),
        sec(head("", "Common questions") + faq([
            ("Where do you work?", "Every county in South Carolina: " + and_list(county_link(c) for c in counties_by_tier()) + "."),
            ("Can you work while the building is occupied?", "Yes. We schedule noisy work early, stage away from entrances and give tenants notice a week ahead."),
        ])),
        cta("Get a commercial roof assessment", "Photos, options and pricing your owner or board can act on."),
    ]
    return {"path": "/commercial/", "active": "/commercial/", "title": "Commercial Roofing in South Carolina: Flat Roof Repair, Restoration & Replacement | Magnolia Roofing",
            "desc": "Commercial roofing for offices, churches, retail, warehouses and apartments across South Carolina. Flat roof repair, coatings, metal and replacement with photo reports.",
            "h1": "Commercial roofing", "sub": "Flat, metal and shingle roofs for occupied buildings across South Carolina.",
            "hero_img": PHOTOS["hero_commercial"]["src"], "body": "".join(body)}


def government():
    who = [
        {"h": "State agencies &amp; colleges", "p": "Through SC state procurement and each campus's purchasing office."},
        {"h": "Counties", "p": "Courthouses, administration buildings, fire and EMS stations, maintenance shops and libraries."},
        {"h": "Cities, towns &amp; municipalities", "p": "Town halls, police and fire stations, public works shops, parks and recreation buildings."},
        {"h": "School districts", "p": "Gyms, classroom wings and field houses, scheduled around the school calendar and summer break."},
        {"h": "Housing authorities", "p": "Scattered-site and multifamily reroofs, unit-by-unit repairs and turnover work."},
        {"h": "Special purpose districts", "p": "Water and sewer, fire, recreation and airport districts."},
    ]
    body = [
        sec(head("For procurement officers, facility directors and project managers", "State, county, city &amp; municipal roofing",
                 "We bid public roofing work statewide: IFBs, RFPs, RFQs, quotes and on-call term contracts. We read the whole solicitation, come to the pre-bid, ask our questions in writing, and turn in a complete, responsive bid. We also sub on public jobs for general contractors.")
            + cards(who)),
        sec(head("What we bring to a public bid", "The paperwork is part of the job") + '<div class="grid two"><div class="card"><h3>Up front</h3>' + ticks([
            f"SC license: {F('number and classification')}",
            f"Bid bonds and performance and payment bonds: {F('surety and capacity')}",
            f"Insurance: {F('GL / auto / umbrella limits')}, certificate naming the agency on request",
            f"Registered vendor: {F('SCBO / SCEIS, county and district portals: list them')}",
            f"Small, minority or woman-owned status: {F('if any certifications apply')}",
        ]) + '</div><div class="card"><h3>During the job</h3>' + ticks([
            "Submittals: product data, shop drawings, installer letters, sample warranty",
            "Safety plan, daily logs and photos to your project manager",
            f"{F('Prevailing wage / Davis-Bacon certified payroll')} when the funding requires it",
            "Change orders priced at bid unit prices, with photos",
            "Closeout binder: warranties, lien waivers, as-builts, O&M data, final photo set",
        ]) + "</div></div>", "tint"),
        sec(head("Case study", "A public reroof, start to finish") + cards([case_card(CASES[1]), case_card(CASES[0])], "grid two")),
        sec(head("Other ways to work with us", "Not everything needs a formal bid") + cards(cls="grid two", items=[
            {"h": "Small purchases & quotes", "p": "Repairs under your formal-bid threshold, quoted in writing with photos, fast."},
            {"h": "On-call / term contracts", "p": "Unit pricing for leak calls, repairs and inspections across all your buildings for a year or more."},
            {"h": "Roof condition assessments", "p": "Photo inventory of your buildings with remaining life and budget estimates for capital planning and bond referendums."},
            {"h": "Emergency response", "p": f"Storm damage and active leaks. {F('Response commitment')}. Call {PHONE}."},
        ])),
        sec(head("References", "Agencies we've worked for") + f"<p>{F('List public clients, contract names, years and a contact who agreed to be a reference')}</p>", "tint"),
        sec(head("", "Common questions") + faq([
            ("Where do you bid?", "Statewide: state agencies, school districts, special purpose districts and every city, town and county, including " + and_list(county_link(c) for c in counties_by_tier()) + "."),
            ("Do you sub on public jobs?", "Yes. We work as the roofing sub for general contractors on public projects, with the paperwork a public owner expects."),
        ])),
        cta("Have a solicitation coming up?", "Send us a message with the solicitation number or a link. We'll confirm we got it the same day."),
    ]
    return {"path": "/government/", "active": "/government/", "title": "State, County, City & Municipal Roofing Contractor in South Carolina | Magnolia Roofing",
            "desc": "Roofing contractor for South Carolina state agencies, counties, cities and municipalities, school districts and housing authorities. IFB/RFP bids, bonding, submittals, prevailing wage and closeout.",
            "h1": "Municipal & government roofing", "sub": "State, county, city and municipal roofing: public bids, term contracts and emergency repairs.",
            "hero_img": PHOTOS["hero_government"]["src"], "body": "".join(body)}


def real_estate():
    offer = [
        {"sym": "Sellers & listing agents", "h": "Pre-listing roof check", "p": "Find and fix roof issues before the buyer's inspector does, so they don't become a negotiating point."},
        {"sym": "Under contract", "h": "Inspection repairs before closing", "p": "Send us the report. We look the same or next day, price each item separately, and fix them before your deadline."},
        {"sym": "Proof for the other side", "h": "Photo report keyed to the inspection", "p": "Every inspection item with a before photo, an after photo and what we did. One PDF for both agents."},
        {"sym": "Buyers & buyer's agents", "h": "Second opinion on a roof", "p": "The inspector flagged the roof. We tell you whether it's a $400 repair or a replacement, with photos, so you can negotiate on facts."},
        {"sym": "Written condition", "h": "Roof condition letter", "p": f"Estimated remaining life and condition in writing, for buyers, lenders and insurers. {F('confirm Joe offers this and the price')}"},
        {"sym": "Insurance", "h": "Roof photos for insurance quotes", "p": "Some insurers want roof age and condition before they'll write a policy. We document it."},
    ]
    pm = [
        "One call for leaks, storm damage, roofs, siding and gutters across your whole portfolio",
        "Photo report after every visit, so you can approve work without driving out",
        "We coordinate with tenants for access",
        f"Separate invoice per property, or per owner. {F('net terms?')}",
        "Turnover inspections and annual roof checks for HOAs and owners",
        "Phased replacement plans across buildings so owners can budget",
    ]
    body = [
        sec(head("Realtors, sellers, buyers and property managers", "The roofer agents call before closing",
                 "Realtors have used Magnolia for inspection repairs since we opened. Here's why: we show up fast, we price each item separately, and we put it in writing with photos so the other side signs off.")
            + quotes(["hemphill", "kim", "royall", "polinsky"])),
        sec(f'<div class="split"><div>{head("Recognized by Realtors", "2025 CCRA Affiliate of the Year")}'
            "<p>The Central Carolina Realtors Association named Magnolia its 2025 Affiliate of the Year. We sponsor the CCRA golf tournament, gala and Circle of Excellence Awards, because Realtors are a big part of how we've grown.</p>"
            f'</div><div>{img("realtor_award")}</div></div>'),
        sec(head("For agents, sellers and buyers", "What we do around a sale") + cards(offer), "tint"),
        sec(f'<div class="split"><div>{head("Closing on a deadline?", "How inspection repairs work")}'
            + steps([("Send the report", "Email or text the inspection report and the closing date."),
                     ("Same or next day", "We go out, photograph each roof item and price it line by line."),
                     ("Fix", "Repairs scheduled around your deadline, not ours."),
                     ("Proof", "PDF report keyed to the inspection items, plus an invoice for the closing attorney.")])
            + f'</div><div>{quote(*R["horton"])}<br>{quote(*R["pound"])}</div></div>'),
        sec(head("Case study", "Seven days to closing") + cards([case_card(CASES[2])], "grid two"), "tint"),
        sec(f'<div class="split flip"><div>{img("crew_ridge")}</div><div>{head("Property managers & landlords", "One roofer for every door")}{ticks(pm)}'
            f'<p>{quote(*R["duque"])}</p></div></div>'),
        sec(head("Agents", "Want a direct line?",
                 f"Agents and property managers get {F('a direct cell / priority scheduling / a dedicated email')}. Tell us who you are and we'll set you up.")
            + BTNS, "tint"),
        sec(head("", "Questions agents ask") + faq([
            ("How fast can you get out?", f"Usually {F('same or next business day')} for inspection repairs. Tell us the closing date when you call."),
            ("Do you give a roof certification?", F("Confirm wording: condition letter / certification, what it covers, how many years, price")),
            ("Will you work with the seller and buyer's agent?", "Yes. We send the same photo report to both sides so there's one set of facts."),
            ("Can the closing attorney pay you?", F("Confirm: can invoices be paid at closing?")),
            ("What areas do you cover?", "All of South Carolina: " + and_list(county_link(c) for c in counties_by_tier()) + "."),
        ])),
        cta("Closing coming up?", "Send us a message with the inspection report and closing date. We'll look at it today."),
    ]
    return {"path": "/real-estate/", "active": "/real-estate/", "title": "Roof Inspection Repairs Before Closing | Realtors & Property Managers, South Carolina | Magnolia Roofing",
            "desc": "Inspection repairs before closing, pre-listing roof checks, roof condition letters and property management roofing across South Carolina. Trusted by local Realtors.",
            "h1": "Real estate & property managers", "sub": "Inspection repairs before closing, roof letters and one roofer for your whole portfolio.",
            "hero_img": PHOTOS["hero_real_estate"]["src"], "body": "".join(body)}


def about():
    people = [
        {"img": "ccra_gala", "h": "Joe Nettles", "sym": "Owner", "p": "Born and raised in the Lowcountry, Joe graduated from the University of South Carolina and has called the Midlands home for more than two decades. He's been roofing for decades and started Magnolia in 2018. " + F("Confirm which person in this photo is Joe.")},
        {"img": "placeholder_1", "h": "Lauren", "sym": F("role"), "p": F("One or two lines about Lauren")},
        {"img": "placeholder_2", "h": "Doug", "sym": F("role"), "p": F("One or two lines about Doug")},
        {"img": "placeholder_3", "h": "Teirnan", "sym": F("role"), "p": F("One or two lines about Teirnan")},
    ]
    community = [
        {"img": "fireflies_wall", "sym": "Columbia Fireflies", "h": "Corporate sponsor at Segra Park", "p": "Magnolia is a Columbia Fireflies corporate sponsor. Look for our sign on the outfield wall, and for the Magnolia and Fireflies swag and thunder sticks we've handed out at games."},
        {"img": "realtor_award", "sym": "Central Carolina Realtors Association", "h": "2025 Affiliate of the Year", "p": "CCRA named Magnolia its 2025 Affiliate of the Year. We've sponsored the CCRA golf tournament at Windermere, the 2024 gala and the 2025 Circle of Excellence Awards."},
        {"img": "veteran_roof", "sym": "Veterans", "h": "A free roof for a veteran in need", "p": "We gave a roof away to a deserving military veteran nominated by the community, and the Magnolia Boys had a booth at the SC Veterans Expo at the State Fairgrounds."},
        {"img": "habitat", "sym": "Habitat for Humanity", "h": "Brew 2 Build", "p": "A sponsor of Central South Carolina Habitat for Humanity's Brew 2 Build craft beer festival."},
        {"img": "placeholder_1", "sym": "Women's rugby", "h": F("Team name"), "p": F("What Magnolia does for the team and since when. Add a photo; we didn't find this one on Facebook.")},
        {"img": "special_olympics", "sym": "Special Olympics SC", "h": "Christmas ornament fundraiser", "p": "Every year our wooden Christmas ornaments raise money. In 2019 the proceeds went to Special Olympics South Carolina."},
    ]
    body = [
        sec(f'<div class="split"><div>{head("Locally and family owned", "South Carolina roofers, not storm chasers")}'
            f'<p>Magnolia Roofing &amp; Remodeling is a locally and family-owned roofing company in Columbia, SC, started by Joe Nettles in 2018.</p>'
            "<p>Joe was born and raised in the Lowcountry, graduated from the University of South Carolina and has called the Midlands home for more than two decades. He'd been roofing for decades before he started his own company.</p>"
            "<p>We're based on St. Andrews Road and work across South Carolina on homes, businesses, churches and public buildings.</p>"
            "<p>Most of our work comes from referrals: neighbors, Realtors and repeat customers. Over 130 reviews say the same things. We answer the phone, we tell the truth about what a roof needs, and the owners come back to check the work.</p>"
            "<p>As our 2026 award post put it, the recognition belongs to the whole Magnolia family: the crews, the team behind the scenes, the Realtors and partners who put their names behind ours, and every homeowner who trusted us with their home.</p>"
            f'<p>{F("A line or two from Joe in his own words")}</p></div><div>{img("team_award", "pic natural")}</div></div>'),
        sec(head("Recognition", "Awards and press") + cards([
            {"img": "states_best", "sym": "The State", "h": "The State's Best roofer, 2025 &amp; 2026", "p": "Voted the Midlands' best roofer by readers of The State newspaper two years in a row."},
            {"img": "realtor_affiliate", "sym": "CCRA", "h": "2025 Affiliate of the Year", "p": "From the Central Carolina Realtors Association."},
            {"img": "owner_truck", "sym": "Our Town Magazine", "h": "Cover story", "p": "Featured on the cover of Our Town Magazine (Lexington)."},
        ]) + f'<p style="margin-top:16px">{F("Other memberships: BBB rating, chamber of commerce, manufacturer certifications (IKO, GAF Weather Stopper, Owens Corning, CertainTeed ShingleMaster logos appear on the old site). Confirm which are current.")}</p>', "tint"),
        sec(head("The team", "The people who answer when you call", "The office team schedules your inspection, answers your questions and keeps your job on track from the first call to the final walk.") + cards(people, "grid four")),
        sec(head("Community", "Part of the community, not just working in it",
                 "From the ballpark to the rugby pitch, Magnolia shows up for the community that has kept us busy since day one.") + cards(community)
            + photos(["golf_tent", "fireflies_park", "team_tent", "golf_nail", "veterans_expo", "golf_hole"]), "tint"),
        sec(head("What people say", "") + quotes(["romlein", "adams"])),
        cta(),
    ]
    return {"path": "/about/", "active": "/about/", "title": "About Magnolia Roofing & Remodeling: Locally and Family-Owned South Carolina Roofer",
            "desc": "Magnolia Roofing & Remodeling is a locally and family-owned South Carolina roofer based in Columbia: The State's Best roofer 2025 and 2026, CCRA 2025 Affiliate of the Year, and a Columbia Fireflies sponsor.",
            "h1": "About Magnolia", "sub": "Locally and family owned in South Carolina.",
            "hero_img": PHOTOS["hero_about"]["src"], "body": "".join(body)}


def case_index():
    body = [sec(SAMPLE_NOTE + head("Case studies", "How we handle real jobs", "Each one walks through the problem, the options and their prices, what we did and what it cost.")
                + cards([case_card(c) for c in CASES])), cta()]
    return {"path": "/case-studies/", "title": "Roofing Case Studies | Magnolia Roofing", "desc": "Commercial, government and real estate roofing case studies from Magnolia Roofing & Remodeling.",
            "h1": "Case studies", "body": "".join(body), "noindex": True, "hero_img": PHOTOS["hero_case_county"]["src"]}


def services_hub():
    body = [sec(head("", "Find the right page", "We split services by who they're for.") + cards(cls="grid four", items=[
        {"href": "/residential/", "img": "house_after", "h": "Homeowners", "p": "Leaks, storm damage, insurance claims and roof replacement."},
        {"href": "/commercial/", "img": "flat_coated", "h": "Commercial", "p": "Flat, metal and shingle roofs for businesses, churches and apartments."},
        {"href": "/government/", "img": "crew_tearoff", "h": "Government", "p": "Public bids and term contracts for SC agencies."},
        {"href": "/real-estate/", "img": "house_after2", "h": "Real estate & property managers", "p": "Inspection repairs before closing and portfolio roofing."},
    ])), cta()]
    return {"path": "/services/", "title": "Roofing Services in South Carolina | Magnolia Roofing",
            "desc": "Residential, commercial, government and real estate roofing services across South Carolina.", "h1": "Our services", "body": "".join(body)}


# ------------------------------------------------------------------ service areas
def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") + "-sc"


GENERIC = ["roof_new_1", "house_after", "crew_ridge", "flashing_new", "roof_new_2", "house_after2"]
TOWN_PHOTOS = {}  # e.g. "Elgin": ["key", ...] once Joe tags real jobs by town


def tier_of(county_name):
    cov = json.load(open(os.path.join(HERE, "coverage.json")))["counties"]
    return cov.get(county_name.replace(" County", ""), {}).get("tier", "state")


def county_towns(county_name):
    """Town entries (tools/areas.json, type=town) whose county starts with this county's short name."""
    short = county_name.replace(" County", "")
    return [t for t in AREAS if t["type"] == "town" and (t.get("county") or "").startswith(short)]


COUNTY_PHOTOS = {}  # e.g. "Aiken County": ["key", ...] once Joe tags real jobs by county


def county_page(a):
    name = a["name"]
    short = name.replace(" County", "")
    place = f"{name}, SC"
    tier = tier_of(name)
    areas = a.get("areas") or []
    lm = a.get("landmarks") or []
    known = a.get("known_for") or []
    seat = a.get("seat") or (areas[0] if areas else "")
    some = and_list(areas)
    if tier == "core":
        intro = (f"Magnolia Roofing &amp; Remodeling repairs and replaces roofs for homes, businesses and public buildings across {name}"
                 + (f", including {some}" if some else "") + ". We're based in the Midlands, so we're never far away.")
    else:
        intro = (f"Magnolia Roofing &amp; Remodeling handles commercial, government and real estate roofing across {name}"
                 + (f", including {some}" if some else "") + ". Based in the Midlands, we work statewide on business, public and property jobs.")
    local = []
    if seat:
        local.append(f"<p><b>County seat:</b> {seat}</p>")
    if lm:
        local.append(f"<p><b>Around the county:</b> {and_list(lm)}.</p>")
    if known:
        local.append(f"<p><b>Known for:</b> {and_list(k.rstrip('.') for k in known)}.</p>")
    if a.get("housing"):
        local.append(f"<p><b>Homes and buildings:</b> {a['housing']}</p>")
    wx = " ".join(x for x in re.split(r"(?<=\.)\s+", a.get("weather") or "") if "earthquake" not in x.lower()).strip()
    if wx:
        local.append(f"<p><b>Weather that hits roofs here:</b> {wx}</p>")
    chips = (f'<h3>Cities, towns and communities</h3><ul class="chips">' + "".join(f"<li>{re.sub(HEDGE, '', x)}</li>" for x in areas) + "</ul>") if areas else ""
    # towns we researched in detail (former town pages) become sections on the county page
    towns = county_towns(name)
    town_cards = []
    for t in towns:
        bits = []
        if t.get("areas"):
            bits.append("Including " + and_list(t["areas"]) + ".")
        if t.get("landmarks"):
            bits.append("Near " + and_list(t["landmarks"]) + ".")
        if t.get("known_for"):
            bits.append(t["known_for"][0].rstrip(".") + ".")
        town_cards.append({"h": t["name"], "sym": "Roofing in", "p": " ".join(bits) or "&nbsp;"})
    town_sec = sec(head("Towns", f"Roofing in {name} towns") + cards(town_cards), "") if town_cards else ""
    svc = []
    if tier == "core":
        svc.append({"href": "/residential/", "h": "Homes", "p": f"Leak repair, storm and hail damage, insurance claims and new roofs for {short} County homeowners."})
    svc += [
        {"href": "/commercial/", "h": "Businesses &amp; churches", "p": f"Flat, metal and shingle roofs for {short} County offices, shops, churches and apartments."},
        {"href": "/real-estate/", "h": "Real estate", "p": f"Inspection repairs before closing and property management roofing in {short} County."},
        {"href": "/government/", "h": "Public agencies", "p": f"{short} County, city, town and school district roofing bids and repairs."},
    ]
    pics = COUNTY_PHOTOS.get(name) or GENERIC
    pic_note = "" if name in COUNTY_PHOTOS else f'<p>{F(f"Photos below are from around the state. Swap in real {name} jobs as they come in.")}</p>'
    body = [
        sec(head(f"Roofing in {place}", f"{short} County roof repair &amp; replacement", intro) + chips),
        sec(f'<div class="split"><div>{head("Local", f"Working in {name}")}{"".join(local)}</div><div>{img(pics[0])}</div></div>', "tint"),
        town_sec,
        sec(head("What we do here", f"Roofing services in {name}") + cards(cls="grid four" if len(svc) == 4 else "grid", items=svc)),
        sec(head("Projects", f"Recent projects in {name}")
            + f'<p>{F(f"Add 2 or 3 real {name} projects: town or neighborhood, roof type, what was done and before/after photos. This is what makes the page rank.")}</p>'
            + pic_note + photos(pics[1:6]), "tint"),
        cta(f"Need a roofer in {name}?", "Free inspection with photos. Call or send us a message."),
    ]
    sch = business_schema({"areaServed": {"@type": "AdministrativeArea", "name": place}})
    what = "Roof repair, replacement and storm damage for homes and businesses" if tier == "core" else "Commercial, government and real estate roofing"
    return {"path": f"/service-areas/{slug(name)}/", "title": f"Roofing in {name}, SC: Roof Repair & Replacement | Magnolia Roofing",
            "desc": f"{what} in {place}" + (f" ({and_list(areas[:3])})" if areas else "") + ". Locally and family owned. Free inspections: (803) 908-7131.",
            "h1": f"Roofing in {place}", "body": "".join(body), "schema": sch, "hero_img": PHOTOS["hero_areas"]["src"]}


def town_redirects():
    """Old town URLs -> their county page (town content now lives on the county page)."""
    out = []
    for t in AREAS:
        if t["type"] != "town":
            continue
        short = (t.get("county") or "").split(" ")[0]
        if short:
            out.append((f"/service-areas/{slug(t['name'])}/", f"/service-areas/{slug(short + ' County')}/", t["name"]))
    return out


def coverage_map():
    """SC county map, coloured by coverage tier (tools/coverage.json). Drawn as inline SVG at build time."""
    import math
    geo = json.load(open(os.path.join(HERE, "sc-counties.geojson")))
    cov = json.load(open(os.path.join(HERE, "coverage.json")))["counties"]
    lat0 = 33.6
    kx = math.cos(math.radians(lat0))
    rings = []
    for f in geo["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        rings.append((f["properties"]["name"], [ring for poly in polys for ring in poly]))
    xs = [x * kx for _, rs in rings for r in rs for x, _ in r]
    ys = [-y for _, rs in rings for r in rs for _, y in r]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    W = 1000
    sc = W / (maxx - minx)
    H = round((maxy - miny) * sc)
    pages = {a["name"].replace(" County", ""): f'/service-areas/{slug(a["name"])}/' for a in AREAS if a["type"] == "county"}
    towns = {a["name"].replace(" County", ""): [re.sub(HEDGE, "", x) for x in (a.get("areas") or [])] for a in AREAS if a["type"] == "county"}
    paths = []
    for name, rs in sorted(rings):
        d = "".join("M" + "L".join(f"{(x * kx - minx) * sc:.1f},{(-y - miny) * sc:.1f}" for x, y in r) + "Z" for r in rs)
        c = cov.get(name, {"tier": "state", "jobs": None})
        data = json.dumps({"name": name, "tier": c["tier"], "jobs": c["jobs"], "page": pages.get(name), "towns": towns.get(name, [])})
        paths.append(f'<path class="cv-{c["tier"]}" d="{d}" tabindex="0" role="button" aria-label="{name} County" data-c=\'{html.escape(data, quote=False)}\'><title>{name} County</title></path>')
    legend = ('<ul class="cv-legend">'
              '<li><i class="cv-core"></i><b>Residential</b><span>' + and_list(c + " County" for c in counties_by_tier("core")) + ', plus commercial, government and real estate</span></li>'
              '<li><i class="cv-state"></i><b>Commercial, government &amp; real estate</b><span>Every other county in South Carolina</span></li></ul>')
    panel = ('<div class="cv-panel" aria-live="polite"><div class="cv-default"><span class="eyebrow">Coverage</span><h3>Statewide</h3>'
             '<p>See what types of customers and services we support in different areas.</p>' + legend + '</div><div class="cv-detail" hidden></div></div>')
    svg = (f'<svg class="cv-map" viewBox="0 0 {W} {H}" role="group" aria-label="Map of South Carolina counties coloured by Magnolia\'s coverage">'
           + "".join(paths) + "</svg>")
    js = """<script>(function(){var m=document.querySelector('.cv-map');if(!m)return;var p=document.querySelector('.cv-panel'),d=p.querySelector('.cv-detail'),def=p.querySelector('.cv-default');
var L={core:'Residential + all services',state:'Commercial, government & real estate'};
var SV={core:['Residential','Real estate','Commercial','Government'],state:['Commercial','Government','Real estate']};
var HREF={Residential:'/residential/','Real estate':'/real-estate/',Commercial:'/commercial/',Government:'/government/'};
function show(el){[].forEach.call(m.querySelectorAll('.on'),function(x){x.classList.remove('on')});el.classList.add('on');m.appendChild(el);
var c=JSON.parse(el.getAttribute('data-c'));var jobs=c.jobs==null?'':'<p class="cv-jobs"><b>'+c.jobs+'</b> jobs completed</p>';
var svc='<ul class="cv-svc">'+(SV[c.tier]||SV.state).map(function(n){return '<li><a href="'+HREF[n]+'">'+n+'</a></li>'}).join('')+'</ul>';
var T=c.towns,t=T.length?'<p class="cv-towns">'+(T.length>1?T.slice(0,-1).join(', ')+' and '+T[T.length-1]:T[0])+'</p>':'';
d.innerHTML='<span class="eyebrow">'+(L[c.tier]||L.state)+'</span><h3>'+c.name+' County</h3>'+svc+jobs+t+(c.page?'<p><a class="cv-more" href="'+c.page+'">Roofing in '+c.name+' County &rarr;</a></p>':'')+'<p><button type="button" class="cv-back">Show legend</button></p>';
d.hidden=false;def.hidden=true;}
m.addEventListener('click',function(e){var el=e.target.closest('path');if(el)show(el)});
m.addEventListener('keydown',function(e){if((e.key==='Enter'||e.key===' ')&&e.target.matches('path')){e.preventDefault();show(e.target)}});
p.addEventListener('click',function(e){if(e.target.closest('.cv-back')){d.hidden=true;def.hidden=false;[].forEach.call(m.querySelectorAll('.on'),function(x){x.classList.remove('on')})}});
})();</script>"""
    return f'<div class="cv">{svg}{panel}</div>{js}'


def areas_index():
    counties = sorted((a for a in AREAS if a["type"] == "county"), key=lambda a: a["name"])
    rows = "".join(
        f'<li><a href="/service-areas/{slug(a["name"])}/">{a["name"]}</a>'
        + (f'<span>{and_list(a.get("areas") or [])}</span>' if a.get("areas") else "") + "</li>"
        for a in counties)
    body = [sec(head("Where we work", "Roofing across South Carolina", "Based in the Midlands, we can easily serve customers from around the state.")
                + coverage_map()),
            sec(head("", f"All {len(counties)} counties", "Each county page covers the towns, landmarks and weather that matter for roofs there.")
                + f'<ul class="county-list">{rows}</ul>', "tint"),
            cta()]
    return {"path": "/service-areas/", "title": "Service Areas: South Carolina Roofing by County | Magnolia Roofing",
            "desc": "Magnolia Roofing coverage map: commercial, government and real estate roofing in every South Carolina county, and residential roofing in the Midlands and Lowcountry. Find your county.",
            "h1": "Service areas", "body": "".join(body)}


def pages():
    out = [residential(), commercial(), government(), real_estate(), about(), case_index(), services_hub(), areas_index()]
    out += [case_page(c) for c in CASES]
    out += [county_page(a) for a in AREAS if a["type"] == "county"]
    return out


# ---------- Home page: "What kind of roof job is it?" router + logo strip ----------
# build_pages.py writes these between <!-- mr:home-jobs --> markers in index.html.
JOBS = [
    {"href": "/residential/", "img": "hero_residential", "who": "Homeowners", "h": "Residential", "btn": "Residential roofing",
     "items": ["Leak repair", "Storm, hail &amp; insurance claims", "Roof replacement", "Siding, trim &amp; gutters"]},
    {"href": "/commercial/", "img": "hero_commercial", "who": "Businesses, churches &amp; apartments", "h": "Commercial", "btn": "Commercial roofing",
     "items": ["Flat &amp; low-slope roofs", "Metal roofs", "Restoration &amp; coatings", "Subcontracting for GCs"]},
    {"href": "/government/", "img": "flat_coated", "who": "State, county, city &amp; municipal", "h": "Government", "btn": "Government roofing",
     "items": ["Public bids &amp; solicitations", "Term contracts", "Emergency repairs", "Schools &amp; housing authorities"]},
    {"href": "/real-estate/", "img": "hero_real_estate", "who": "Realtors &amp; property managers", "h": "Real estate", "btn": "Real estate roofing",
     "items": ["Inspection repairs before closing", "Pre-listing roof checks", "Roof condition letters", "Photo reports for both sides"]},
]


def home_jobs():
    cards_html = "".join(
        f'<a class="mr-job" href="{j["href"]}"><span class="mr-job-pic">{card_img(j["img"])}</span>'
        f'<span class="mr-job-body"><span class="eyebrow">{j["who"]}</span><h3>{j["h"]}</h3>'
        f'<ul class="ticks">{"".join(f"<li>{i}</li>" for i in j["items"])}</ul>'
        f'<span class="theme-button hvr-grow-shadow mr-btn-pri mr-job-btn">{j["btn"].upper()}</span></span></a>'
        for j in JOBS)
    jobs = (f'<section class="mr-jobs"><div class="wrap"><div class="mr-jobs-card">'
            f'{head("", "What kind of roof job is it?", "Pick the one that fits. Each page shows the jobs we do for you, how we work and what to expect.")}'
            f'<div class="mr-jobs-grid">{cards_html}</div></div></div></section>')
    return f'<div class="grid-row mp" style="padding:0">{jobs}{home_logos()}</div>'


def home_logos():
    logos = json.load(open(os.path.join(os.path.dirname(__file__), "logos.json"), encoding="utf-8"))
    import hashlib
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for l in logos:  # small copy (tools/perf.py) when there is one; cache-bust so a fixed logo shows up right away
        small = os.path.splitext(l["src"])[0] + ".logo.webp"
        if os.path.exists(os.path.join(root, small.lstrip("/"))):
            l["src"] = small
        f = os.path.join(root, l["src"].lstrip("/"))
        if os.path.exists(f):
            wh = img_size(f)
            l["wh"] = f' width="{wh[0]}" height="{wh[1]}"' if wh else ""  # aspect ratio only (CSS sets the size): no shift on load
            l["src"] += "?v=" + hashlib.md5(open(f, "rb").read()).hexdigest()[:8]
    one = "".join(f'<li><img src="{l["src"]}" alt="{l["alt"]}"{l.get("wh", "")}></li>' for l in logos)
    reps = max(1, -(-12 // len(logos)))          # fill at least ~12 slots so one set is wider than the screen
    track = one * reps
    hidden = "".join(f'<li aria-hidden="true"><img src="{l["src"]}" alt=""{l.get("wh", "")}></li>' for l in logos) * reps  # loop copy
    secs = len(logos) * reps * 6                 # ~6s per logo
    return (f'<section class="mr-logos" aria-label="Certifications, memberships and community partners">'
            f'<div class="mr-logos-viewport"><ul class="mr-logos-track" style="--dur:{secs}s">{track}{hidden}</ul></div></section>')
