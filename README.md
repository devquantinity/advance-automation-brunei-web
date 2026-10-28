# Advance Automation Sdn Bhd – website

Static rebuild of <https://advanceautomationbrunei.com> on the Veltom template.
Every URL of the live site exists here under the same address.

## What is where

| Path | What it is |
| --- | --- |
| `index.html`, `404.html`, `about-us/`, `clients/`, `contact/`, `news-n-events/`, `products-and-services/` | **The site.** One folder per URL of the live site (`/about-us` is `about-us/index.html`), so the clean URLs work on any static host without rewrite rules. |
| `css/`, `js/`, `images/`, `fonts/`, `videos/`, `documents/` | Assets. `css/aab.css` and `js/aab.js` hold everything that is specific to this site; `images/aab/` holds Advance Automation's own pictures. |
| `_template/` | The Veltom demo pages. Design reference and the source of every section used on the site. **Not part of the site.** |
| `source-site/` | The scrape of the live site (pages, pictures, `CONTENT.md`). Source of every text and picture. **Not part of the site.** |
| `_build/` | The generator that assembles the pages. **Not part of the site.** |

## Preview

Links are root-relative (`/about-us`), so open the pages through a web server, not from the Finder:

```
python3 -m http.server 8000        # in this folder, then http://localhost:8000/
```

## How the pages are made

Each page is a sequence of sections taken unchanged from `_template/`, filled with the text and pictures of the
matching live page from `source-site/`. No section is designed from scratch and no copy is written: a template
section that has no real content to show is left out.

```
python3 _build/build.py            # writes every page (or: build.py home about …)
python3 _build/check.py            # links, assets, leftover template sample content
```

Needs Python 3 with `beautifulsoup4`, `html5lib`, `Pillow`, `numpy`, and Node with `npm install` run once in
`_build/` (Prettier 3.3.3, the formatter behind webformatter.com/html, with the same settings).

The pages are generated files: a manual edit is overwritten by the next build. Change the source instead:

| To change | Edit |
| --- | --- |
| Menu, footer, phone numbers, e-mail addresses, address, opening hours | `_build/shared.py` |
| Text the client asked to change on top of the live site's text | `_build/client_changes.py` |
| Which sections a page uses and what goes into them | `_build/pages.py` |
| Page list, certificate captions, banner pictures | `_build/site_data.py`, `BANNERS` in `_build/shared.py` |
| Spacing or styling of something specific to this site | `css/aab.css` |
| How the live pages are read | `_build/aabcontent.py` |

## Pages and the template sections they use

| Page | Sections (template page they come from) |
| --- | --- |
| `/` | hero (home-two hero, already on home-one) · logo strip · experts-v3 · exterior band (service-two) · team cards (about-two) for the three certificates · solutions-v4 · about-v1 · complex-v1 counters · blog-v2 |
| `/about-us` | hero-v12 (blog) · experts-v3 (home-one) · about-v3 (about-two) · expertise-v2 (about-two) · complex-v1 counters (home-one) |
| `/products-and-services` | hero-v12 · support-v1 cards (about-three) |
| the 4 category pages | hero-v12 · capabilities-v1 (service-one) |
| the 19 product and service pages | hero-v12 (blog-post) · blog-information rich text (blog-post) |
| `/news-n-events` | hero-v12 · blog-v1 cards (blog) |
| the 8 news items | hero-v12 (blog-post) · blog-information · blog-v3 "Latest news" (blog-post) |
| `/clients` | hero-v12 · complex-v1 tiles (home-one) |
| `/contact` | hero-v12 · contact-v1 · contact-v2 (contact) |
| `404.html` | utility page (404) |

Navigation bar and footer are the template's, with the live site's menu and contact details.

## Changes to the template's own files

- `js/site.schunk.ef3d838b12b5ed87.js` – four changes, described in the comment on its first line (interactions are
  no longer tied to one page, so a section animates on whichever page uses it; the logo strip keeps its pace with
  eleven logos; the "Our services" cards on the home page no longer react to hover - `js/aab.js` opens them one by
  one as the page scrolls, and on desktop they slide in together).
- `css/veltom.shared.7640c260e.css` – untouched. All additions are in `css/aab.css`.

## Going live

- Upload everything except `_template/`, `_build/`, `source-site/` and this file (`robots.txt` keeps search engines
  out of those folders if they are uploaded anyway).
- Links and canonical tags use the live site's addresses (`/about-us`, no trailing slash). A plain Apache or nginx
  host answers such an address with a redirect to `/about-us/` and then serves the page; nothing else is needed.
- `404.html` is picked up automatically by hosts such as Netlify or GitHub Pages; on Apache add
  `ErrorDocument 404 /404.html` to `.htaccess`.
- The contact form has no server behind it yet: it opens the visitor's mail program with the message addressed to
  `sales@advanceautomationbrunei.com`. To use a form handler, set `action` and `method` in `build_contact()` in
  `_build/pages.py`.
- Copy is taken from the live site as it is, typing mistakes included (for example "devlivery", "Commiting",
  "Callibrates", "Equipmentm"). Correct them in `source-site/pages/` or on the live site and build again.
# advance-automation-brunei-web
