"""Navigation, footer and the inner-page banner (all taken from the template, filled with the live site's menu and details)."""
from core import *

COMPANY = 'Advance Automation Sdn Bhd'
PHONES = [('+673-8278-288', '+6738278288'), ('+673-8271-332', '+6738271332'), ('+673-3201-332', '+6733201332')]
FAX = '+673-8271-332'
EMAIL = 'sales@advanceautomationbrunei.com'
ADDRESS = ['Unit B1, Block 3,', 'Komplex Perindustrian Pekan Belait.', 'Spg 114, KA3131, Kuala Belait', 'P.O.Box. 168, KB1133, Seria', 'Negara Brunei Darussaalam']
ISO_LINE = 'ISO 9001:2015 - ISO 14001:2015 Certified'
MOTTO = 'Service with an Honest faith'
HOURS = [('Monday to Thursday', ['8:00am - 5:00pm']), ('Friday', ['8:00am - 12:00pm', '2:00pm - 5:00pm']), ('Saturday and Sunday, PH', ['Closed'])]
COPYRIGHT = 'Copyright © 2011 - 2025 Advance Automation Sdn Bhd. All Rights Reserved.'
CREDIT = ('Site developed &amp; maintained by ', 'Gotka Technologies', 'https://gotka.com/clients/aff.php?aff=18', 'Gotka Technologies - We Bring your business online')

# the live site's menu (labels exactly as there)
CATEGORIES = [
    ('custom-made', 'Custom Made'),
    ('calibration-certification-services', 'Calibration & Certification'),
    ('safety-products', 'Safety Product'),
    ('control-and-instrument-valves', 'Control & Instrument Valves'),
    ('capabilities', 'Capabilities'),
    ('engineering-and-services', 'Engineering And Services'),
]
MENU = [
    ('home', 'Home', '/'),
    ('about', 'About us', '/about-us'),
    ('products', 'Products and Services', '/products-and-services'),
    ('clients', 'Clients', '/clients'),
    ('news', 'News and Events', '/news-n-events'),
    ('contact', 'Contact', '/contact'),
]
CTA_LABEL = 'Get in touch'          # heading of the contact block in the live site's footer


def _plain_link(proto, label, href, current):
    a = clone(proto)
    a['href'] = href
    set_text(a.select_one('.fda-menu-text'), label)
    cls = [c for c in a.get('class', []) if c != 'w--current']
    if a.has_attr('aria-current'): del a['aria-current']
    if current:
        cls.append('w--current'); a['aria-current'] = 'page'
    a['class'] = cls
    return a


def nav(active, variant_page='contact.html'):
    """Template navigation bar with the live site's menu.  active = key of the current top-level item."""
    n = sec(variant_page, 'div.fda-navbar')
    top = n.select_one('.fda-navigation-top')
    kids = top.find_all(True, recursive=False)
    home_proto = kids[0]                                   # plain link
    dd_proto = kids[1]                                     # single-list dropdown ("about")
    for k in kids:
        k.extract()
    link_protos = dd_proto.select('a.fda-nav-link-wrapper')
    for key, label, href in MENU:
        if key != 'products':
            top.append(_plain_link(home_proto, label, href, active == key))
            continue
        dd = clone(dd_proto)
        set_text(dd.select_one('.fda-menu-wrap .fda-menu-text'), label)
        box = dd.select_one('.fda-nav-mega-menu-list-box-wrapper')
        box.clear()
        entries = [(label, href)] + [(lab, f'/products-and-services/{slug}') for slug, lab in CATEGORIES]
        for i, (lab, h) in enumerate(entries):
            a = clone(link_protos[i % len(link_protos)])
            a['href'] = h
            d = a.select_one('.fda-nav-dropdown-link')
            d['class'] = ['fda-nav-dropdown-link'] + (['fda-top'] if i == 0 else []) + (['fda-buttom-0'] if i == len(entries) - 1 else [])
            set_text(d, lab)
            for k in ('aria-current',):
                if a.has_attr(k): del a[k]
            a['class'] = [c for c in a.get('class', []) if c != 'w--current']
            box.append(a)
        top.append(dd)
    # mobile panel: button, video, (template social links removed - the live site has none)
    for a in n.select('.fda-navigation-bottom a.fda-button-main'):
        set_button(a, CTA_LABEL, '/contact')
    soc = n.select_one('.fda-navigation-bottom .fda-nav-mega-left-buttom')
    if soc is not None: soc.decompose()
    # ... and the small stock clip of the mobile panel: decoration with no counterpart on the live site
    vid = n.select_one('.fda-navigation-bottom .fda-nav-tab-video')
    if vid is not None: vid.decompose()
    # right-hand button
    for a in n.select('.fda-nav-button a.fda-button-main'):
        set_button(a, CTA_LABEL, '/contact')
    # logo
    brand = n.select_one('a.fda-brand')
    brand['href'] = '/'
    if active == 'home':
        brand['aria-current'] = 'page'; brand['class'] = brand.get('class', []) + ['w--current']
    else:
        if brand.has_attr('aria-current'): del brand['aria-current']
        brand['class'] = [c for c in brand.get('class', []) if c != 'w--current']
    return n


def footer(active=None):
    f = sec('contact.html', 'section.fda-footer')
    logo = f.select_one('.fda-footer-logo a'); logo['href'] = '/'
    set_text(f.select_one('.fda-discernibale-text div'), COMPANY)
    set_text(f.select_one('.fda-footer-top-center-left > .fda-text-style-h3'), MOTTO)
    set_button(f.select_one('.fda-footer-top-center-left > a.fda-button-main'), CTA_LABEL, '/contact')
    # link column = main menu
    col = f.select_one('.fda-footer-top-content-link')
    protos = col.select('a.fda-footer-link')
    for p in protos: p.extract()
    for i, (key, label, href) in enumerate(MENU):
        a = clone(protos[i % len(protos)])
        a['href'] = href
        set_text(a.select_one('.fda-text-style-h6'), label)
        a['class'] = [c for c in a.get('class', []) if c != 'w--current'] + (['w--current'] if key == active else [])
        if a.has_attr('aria-current'): del a['aria-current']
        if key == active: a['aria-current'] = 'page'
        col.append(a)
    # contact column
    form = f.select_one('.fda-footer-form-link')
    heads = form.select('.fda-form-left-card-heading')
    set_text(heads[0].select_one('.fda-text-style-h6'), 'Get in touch')
    # e-mail row
    set_text(heads[1].select_one(':scope > .fda-text-style-h6'), 'Mail us @ :')
    a = heads[1].select_one('a'); a['href'] = 'mailto:' + EMAIL; set_text(a.select_one('.fda-text-style-h6'), EMAIL)
    # phone row -> three numbers
    set_text(heads[2].select_one(':scope > .fda-text-style-h6'), 'Call us :')
    pa = heads[2].select_one('a'); pa.extract()
    for num, tel in PHONES:
        b = clone(pa); b['href'] = 'tel:' + tel; set_text(b.select_one('.fda-text-style-h6'), num)
        heads[2].append(b)
    # address
    addr = f.select_one('.fda-footer-address-wrapper')
    set_text(addr.select('div')[0], 'Address:')
    set_html(addr.select('div')[1], '<br />'.join(esc(x) for x in ADDRESS))
    # bottom row: copyright + credit (as on the live site); the template's utility links are removed
    bottom = f.select_one('.fda-footer-bottom-wrapper')
    set_html(bottom, f'<div>{esc(COPYRIGHT)} {CREDIT[0]}<a class="fda-text-color-white aab-credit-link" href="{CREDIT[2]}" target="_blank" rel="noopener" title="{CREDIT[3]}">{CREDIT[1]}</a></div>')
    util = f.select_one('.fda-utility-wrapper')
    if util is not None: util.decompose()
    return f


# banner pictures (template library, HD) per area of the site
BANNERS = {
    'about': 'Team-details-banner',
    'products': 'Service-one-banner-a1',
    'custom-made': 'Home-three-banner-v2',
    'calibration-certification-services': 'FAQ-banner',
    'safety-products': 'Service-three-banner-2',
    'control-and-instrument-valves': 'Service-one-automation-3-b',
    'capabilities': 'Home-two-aa-1automation',
    'engineering-and-services': 'Home-three-banner-v3',
    'clients': 'Home-one-banner-image-A1-b',
    'news': 'Blog-banner-image',
    'contact': 'Contact-banner-image',
}


def hero12(label, title, banner, wide=False, own_image=None):
    """Inner-page banner (template: fda-hero-v12).  wide=True uses the blog-post variant made for long titles."""
    if wide:
        h = sec('blog-post/advanced-systems-for-process-improvement.html', 'section.fda-hero-v12')
    else:
        h = sec('blog.html', 'section.fda-hero-v12')
    if label is None:
        h.select_one('.fda-sub-wrap').decompose()
    else:
        set_text(h.select_one('.fda-sub-text'), label)
    set_text(h.select_one('h1'), title)
    img = h.select_one('img.fda-banner-image-animation')
    if own_image:
        img_set(img, own_image, alt=title)
        img['sizes'] = '100vw'
    else:
        use_tpl_img(img, BANNERS[banner], alt=title)
    img['loading'] = 'eager'
    return h
