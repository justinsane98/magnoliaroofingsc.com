# magnoliaroofingsc.com

Static 1:1 clone of the GoSite site at magnoliaroofssc.com, hosted on GitHub Pages.

## Layout
- `index.html`, `services/index.html` — mirrored pages
- `assets/<host>/…` — locally mirrored images, CSS, fonts, and GoSite platform JS (keeps layout/menus/galleries working)
- `assets/site/config.js` — **edit this**: form recipient email, optional Web3Forms key, phone for the chat button
- `assets/site/site.js` — replaces GoSite features: contact form, chat button, privacy popup
- `assets/site/reviews.js` + `reviews.json` — "What Our Clients Say" scrolling reviews + Leave Feedback modal
- `tools/mirror.py` — re-pull from the live GoSite site (`python3 -I tools/mirror.py`). Overwrites the HTML pages.

## Replaced GoSite features (free)
| Feature | Was | Now |
|---|---|---|
| Contact form | GoSite API + reCAPTCHA | [FormSubmit](https://formsubmit.co) → magnoliaroofingsc@gmail.com (first submit sends a one-time activation email) |
| Chat | GoSite Messenger | none — "CHAT NOW!" texts the office on mobile / scrolls to the form on desktop |
| Privacy popup | loaded from GoSite API | static modal in `site.js` |
| GoSite analytics/hit tracker | removed | GA4 `G-3KY2TQVQBH` kept |
| Reviews | 2 static cards (GoSite review widget hidden) | all reviews from `reviews.json`, 3 per page with a drag-to-scrub page slider; snapshot refreshed by `tools/mirror.py` while GoSite is active, edit by hand after |
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
