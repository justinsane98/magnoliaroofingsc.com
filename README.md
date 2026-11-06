# magnoliaroofingsc.com

Static 1:1 clone of the GoSite site at magnoliaroofssc.com, hosted on GitHub Pages.

## Layout
- `index.html`, `services/index.html` — mirrored pages
- `assets/<host>/…` — locally mirrored images, CSS, fonts, and GoSite platform JS (keeps layout/menus/galleries working)
- `assets/site/config.js` — **edit this**: form recipient email, optional Web3Forms key, phone for the chat button
- `assets/site/site.js` — replaces GoSite features: contact form, chat button, privacy popup
- `assets/site/scrubber.js` — shared slider (snap track + burgundy scrubber pill) used by reviews and gallery
- `assets/site/reviews.js` + `reviews.json` — "What Our Clients Say" reviews (year steps on the scrubber) + Leave Feedback modal
- `assets/site/gallery.js` — "Some of Our Work" photo slider + lightbox (mirrored GoSite photos + extras listed in `assets/site/work.json`)
- `assets/site/hero.js` — home hero "The State's Best" 2025/2026 winner badges (CSS-built; swap in official artwork from The State if available)
- `tools/pages_content.py` `JOBS` / `tools/logos.json` — home page "What kind of roof job is it?" cards and the scrolling logo strip (built into `index.html` between `<!-- mr:home-jobs -->` markers by `tools/build_pages.py`)
- `assets/site/work/` — real Magnolia job photos from Facebook (order in `work.json`)
- `tools/mirror.py` `COPY_FIXES` — typo/grammar fixes applied to the mirrored copy
- `tools/mirror.py` — re-pull from the live GoSite site (`python3 -I tools/mirror.py`). Overwrites the HTML pages.
  **Re-run it after editing anything in `assets/site/`** — it stamps `?v=<hash>` on those script/style links so browsers pick up changes.

## Replaced GoSite features (free)
| Feature | Was | Now |
|---|---|---|
| Contact form | GoSite API + reCAPTCHA | [FormSubmit](https://formsubmit.co) → magnoliaroofingsc@gmail.com (first submit sends a one-time activation email) |
| Chat | GoSite Messenger | none — "CHAT NOW!" texts the office on mobile / scrolls to the form on desktop |
| Privacy popup | loaded from GoSite API | static modal in `site.js` |
| GoSite analytics/hit tracker | removed | GA4 `G-3KY2TQVQBH` kept |
| Reviews | 2 static cards (GoSite review widget hidden) | all reviews from `reviews.json`, 3 per page, scrubber with "x–y of 81" and year steps; snapshot refreshed by `tools/mirror.py` while GoSite is active, edit by hand after |
| Leave Feedback | GoSite | modal: name + star rating + message, emailed with the date via the same service as the contact form |
| "Powered by GoSite" footer badge | shown | hidden |
| UserWay accessibility overlay | loaded | removed |

## Still tied to third parties (they keep working after the move, until those accounts are cancelled)
- RealWork Labs "neighborhood" project map plugin
- GTranslate language switcher

## DNS (at the registrar for magnoliaroofingsc.com)
- Apex `A` records: 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153
- `www` `CNAME` → `<github-user>.github.io`
- Later: `app` CNAME → wherever the bid/CRM app is hosted (doesn't affect Pages)
- Old domain magnoliaroofssc.com: 301-forward to https://magnoliaroofingsc.com at its registrar (Pages allows one custom domain per repo).

## Pages built by tools/build_pages.py (Nov 2026)
The site is no longer a pure GoSite mirror. **Don't run `tools/mirror.py` on index.html anymore**: it would overwrite the new home copy and nav.

- `python3 -I tools/build_pages.py` builds `/residential/`, `/commercial/`, `/government/`, `/real-estate/`, `/about/`, `/services/` (a hub), `/case-studies/…` and `/service-areas/…` (11 towns and 9 counties). It also sets the nav on index.html and rewrites `sitemap.xml`.
- Shell: `services/_shell.html` (frozen copy of the original services page) supplies head, header, hero and footer. Copy lives in `tools/pages_content.py`, styles in `assets/site/pages.css`.
- Town and county facts: `tools/areas.json` (researched, with sources). Photos: `tools/photos.json` maps keys to `assets/site/fb/*.jpg` (resized from the Magnolia Facebook page).
- **Yellow dashed text** (`class="fill"`) = a fact Joe still has to supply. Search the built HTML for `class="fill"` to list them.
- **Case studies are SAMPLES**: made-up, labeled on the page, `noindex` and left out of the sitemap. Replace them with real jobs, then drop `"noindex": True` in `case_page()`.
