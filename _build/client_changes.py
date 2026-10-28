"""Changes the client asked for on top of the live site's text.

They are applied to the scraped pages (source-site/pages) as those are read, so every page built from that text shows
the new version, while source-site/ stays an untouched copy of the live site.  Contact details that do not come from the
scrape (footer, contact page) and the ISO line are set in shared.py.

Each entry is (page, old, new): page is the path below source-site/pages without .html, or '*' for every page.  The old
text is matched with any run of white space between its words, because the scraped HTML is wrapped over several lines."""
import re

CHANGES = [
    # 23 Oct 2026, client (WhatsApp): +673 8278288 is no longer shown; +673 3211332 takes its place
    ('*', '(+673) 8278 288', '(+673) 3211 332'),
    ('*', '+673-8278-288', '+673-3211-332'),
    ('*', '+673 8278288', '+673 3211332'),
    ('*', 'tel:+6738278288', 'tel:+6733211332'),
    # 23 Oct 2026: ISO 45001:2018 is listed with ISO 9001 and ISO 14001
    ('*', 'We are ISO 9001:2015 Quality and ISO 14001:2015 Environmental Certified',
     'We are ISO 9001:2015 Quality, ISO 14001:2015 Environmental and ISO 45001:2018 Occupational Health and Safety Certified'),
    # 23 Oct 2026: "Qualifications & Certifications" on the Calibration & Certification page
    ('products-and-services/calibration-certification-services',
     '<li>Certified Technicians</li> <li>Professional Engineers</li> <li>OEM Trained Staff</li>',
     '<li>Certified technician (VILT) IEC 17025:2015</li> <li>Professional Engineer MS Elect, ENG, Sc, Nz</li> '
     '<li>Certified Medical Doctor MBBS</li> <li>OEM Trained Staff</li>'),
    ('products-and-services/calibration-certification-services',
     'Meeting the requirement of Quality Assurance ISO 9001-2008',
     'Meeting the requirement of Quality Assurance ISO 9001:2015, ISO 14001:2015 &amp; ISO 45001:2018'),
]


def apply(rel, html):
    """The scraped page rel with every change for it (and for all pages) applied."""
    for page, old, new in CHANGES:
        if page in ('*', rel):
            html = re.sub(r'\s+'.join(re.escape(w) for w in old.split()), lambda m: new, html)
    return html
