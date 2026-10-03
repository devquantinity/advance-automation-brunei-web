# source-site — scrape of advanceautomationbrunei.com

Everything from the client's current Joomla site, scraped on 30 Sep 2026 to rebuild it on the Veltom template.

## What's here

| Path | What it is |
| --- | --- |
| `CONTENT.md` | All page text in menu order (header, footer, menu, then every page), with local image paths. Start here when writing copy. |
| `pages/` | Raw HTML of all 45 URLs, formatted the same way as the template (Prettier, 4 spaces). Same folder structure as the live URLs. |
| `images/` | 234 images, 23 MB (see below). |
| `manifest.json` | Every original URL → local file, which pages use it, and its alt text. Also lists files that are broken on the live site. |

## Images

| Folder | Files | Notes |
| --- | --- | --- |
| `images/logos/` | 2 | Company logo, full and small |
| `images/cert/` | 4 | ISO 9001 / 14001 / 45001 (ANAB) badge and 3 licence/cert screenshots |
| `images/clients/` | 11 | Client logos (Clients page) |
| `images/slideshow/` | 3 | Home page hero slides |
| `images/services/` | 6 | Home page service cards |
| `images/about_us/` | 3 | About us photos |
| `images/products-services/` | 94 | Product and service photos, by category |
| `images/news_events/` | 24 | News article galleries |
| `images/featured/` | 27 | Lead image of each product/service and news article, original full size, named after its page |
| `images/` (root) | 2 | `bg-img.jpg` (About background), `download.jpg` (Downloads block) |
| `images/theme/` | 10 | Old theme backgrounds (footer, breadcrumb bar), favicon |
| `images/_site-ui/` | 48 | Old CMS/slider UI bits (arrows, bullets, icon fonts). Not needed for the rebuild; kept only for completeness |

## Broken on the live site (nothing to download)

- The two PDFs in the home page "Download files" block return 404: `/download/pdf/AAB-Service-Quality-ADT.pdf` and `/download/pdf/AAD-Quality-Policy.pdf`. Ask the client for these files.
- 5 older images on the Temperature Devices, Dimension Measurement, Valve Repairs and Gerbaru Jaya news pages are 404 (`/images/stories/...`).
- 12 old theme icons referenced only by the old CSS.

## Notes

- 3 URLs are duplicates of another page (listing pagination); `CONTENT.md` lists them at the end instead of repeating them.
- `pages/index.html`: the live page uses invalid `</br>` tags, changed to `<br />` so it could be formatted. Nothing else in `pages/` was edited.
