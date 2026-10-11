"""Page compositions: which template sections each Advance Automation page uses and what goes into them."""
import os, re, html, shutil
from core import *
import shared as S
import site_data as D
import aabcontent as A
import richtext as RT

SRC_IMG = f'{SRC}/images'
POST = 'blog-post/advanced-systems-for-process-improvement.html'
WF = {'home': '69b2a15200bc2cb1d23ead67', 'post': '69b2a15200bc2cb1d23ead7a', 'blog': '69b2a15200bc2cb1d23ead71', 'contact': '69b2a15200bc2cb1d23ead70',
      'about': '69b2a15200bc2cb1d23ead76', 'services': '69b2a15200bc2cb1d23ead6b', 'category': '69b2a15200bc2cb1d23ead6c', '404': '69b2a15200bc2cb1d23ead75'}


def aab_image(sub):
    """Use one of the scraped pictures: copy source-site/images/<sub> to images/aab/<sub> and return the site path."""
    site_path = 'images/aab/' + (sub.replace('services/', '') if sub.startswith('services/') else sub)
    RT.COPIED[site_path] = f'{SRC_IMG}/{sub}'
    return site_path


# ------------------------------------------------------------------ pictures derived from the scraped originals
# Each is made once and then kept in images/aab/ like any other picture of the site (delete the file to have it made again).
def _derived(site_path, make):
    from PIL import Image
    dst = f'{OUT}/{site_path}'
    if not os.path.isfile(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        make(dst)
    with Image.open(dst) as im:
        return site_path, im.size


def share_image():
    """images/aab/og-image.jpg (1200 x 630): the picture link previews show - the live site's plant picture, cropped."""
    from PIL import Image

    def make(dst):
        with Image.open(f'{SRC_IMG}/services/services4.jpg') as im:
            im = im.convert('RGB')
            k = max(1200 / im.width, 630 / im.height)
            im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
            x = (im.width - 1200) // 2; y = (im.height - 630) // 2
            im.crop((x, y, x + 1200, y + 630)).save(dst, quality=86, optimize=True, progressive=True)
    return _derived('images/aab/og-image.jpg', make)


def certificate_card_image(sub, name):
    """Picture for a certificate card.  The scans on the live site are screenshots taken in a PDF viewer: each carries a grey
    frame a few pixels wide and one of them the viewer's comment icon on the corner of the page.  The card shows the page
    only (frame trimmed, icon covered with the paper colour around it); the card links to the untouched scan."""
    from PIL import Image

    def make(dst):
        import numpy as np
        im = Image.open(f'{SRC_IMG}/{sub}').convert('RGB')
        a = np.asarray(im).astype(int)
        rows = np.nonzero(a.mean(axis=(1, 2)) > 215)[0]; cols = np.nonzero(a.mean(axis=(0, 2)) > 215)[0]
        box = (int(cols[0]) + 1, int(rows[0]) + 1, int(cols[-1]), int(rows[-1]))
        im = im.crop(box); a = np.asarray(im).astype(int)
        # viewer icon: saturated orange in the top right corner of the page
        corner = a[:70, -70:]
        r, g, b = corner[..., 0], corner[..., 1], corner[..., 2]
        ys, xs = np.nonzero((r > 190) & (g > 70) & (g < 180) & (b < 110))
        if len(xs) > 40:
            x0 = im.width - 70 + int(xs.min()) - 4; y0 = max(0, int(ys.min()) - 4); y1 = int(ys.max()) + 5
            paper = im.getpixel((x0 - 8, (y0 + y1) // 2))
            im.paste(paper, (x0, y0, im.width, y1))
        im.save(dst, optimize=True)
    return _derived(f'images/aab/cert/{name}.png', make)


def badge_image():
    """The accreditation badge without the transparent margin of the original file; shown 200px wide, so 400px for sharp screens."""
    from PIL import Image

    def make(dst):
        with Image.open(f'{SRC_IMG}/cert/ISO_9001_ISO_14001_ISO_45001_ANAB.png') as im:
            im = im.convert('RGBA')
            box = im.getchannel('A').getbbox()
            if box: im = im.crop(box)
            im.resize((400, round(im.height * 400 / im.width)), Image.LANCZOS).save(dst, optimize=True)
    return _derived('images/aab/iso-anab-badge.png', make)


def plain_text(blocks, limit=400):
    out = []
    for b in blocks:
        if b['t'] in ('p', 'h'):
            out.append(A.plain(b['html']))
        elif b['t'] in ('ul', 'ol'):
            out.extend(A.plain(i['html']) for i in b['items'])
        if sum(len(x) for x in out) > limit:
            break
    return ' '.join(out)


# ------------------------------------------------------------------ article (template: blog post)
def article_section(blocks, card_img, card_alt, card_title, card_href, card_sub, card_sub_href=None, last=False):
    """last=True: the article is the last section of the page (in the template it is always followed by 'New blog posts')."""
    s = sec(POST, 'section.fda-blog-information')
    if last:
        s['class'] = s['class'] + ['aab-last']
    card = s.select_one('.fda-blog-author-wrapper')
    img_set(card.select_one('img'), card_img, alt=card_alt)
    box = card.select_one('.fda-blog-author-name-box')
    name, role = box.find_all('div', recursive=False)
    if card_href:
        name.name = 'a'; name['href'] = card_href        # same pattern as the template's linked card titles
    set_text(name, card_title)
    if card_sub:
        if card_sub_href:
            set_html(role, f'<a class="aab-plain-link" href="{card_sub_href}">{esc(card_sub)}</a>')
        else:
            set_text(role, card_sub)
    else:
        role.decompose()
    right = s.select_one('.fda-blog-information-right-mg')
    kids = right.find_all(True, recursive=False)
    rich = kids[0].select_one('.w-richtext')
    rich['class'] = ['aab-richtext', 'w-richtext']
    set_html(rich, RT.render(blocks))
    for k in kids[1:]:
        k.decompose()
    if not blocks or blocks[0]['t'] != 'h':
        right['class'] = right.get('class', []) + ['aab-no-lead-heading']
    return s


def related_section(heading, cards, button_label='Read more'):
    """Two cards under an article (template: 'New blog posts')."""
    s = sec(POST, 'section.fda-blog-v3')
    set_text(s.select_one('h2'), heading)
    items = s.select('.w-dyn-item')
    proto = items[0]
    lst = proto.parent
    for it in items: it.extract()
    for c in cards:
        it = clone(proto)
        a_img = it.select_one('a.fda-blog-v1-item-image'); a_img['href'] = c['href']
        card_picture(a_img.select_one('img'), c)
        date = it.select_one('.fda-blog-v1-publish-date')
        if c.get('date'):
            set_text(date.find_all('div', recursive=False)[-1], c['date'])
        else:
            date.decompose()
        t = it.select_one('a.fda-text-style-h4'); t['href'] = c['href']; set_text(t, c['title'])
        set_button(it.select_one('a.fda-button-main'), button_label, c['href'])
        lst.append(it)
    return s


def news_card_data(slug):
    n = [x for x in D.NEWS if x['slug'] == slug][0]
    return {'href': f'/news-n-events/item/{slug}', 'img': aab_image(f'featured/{slug}.jpg'), 'title': n['title'], 'date': D.news_date(slug),
            'contain': slug in D.NEWS_GRAPHICS}


def card_picture(img, c):
    """Picture of a news card.  A graphic (a logo on white) is shown whole instead of being cropped to the card."""
    img_set(img, c['img'], alt=c['title'])
    if c.get('contain'):
        img['class'] = img.get('class', []) + ['aab-contain']
    return img


def build_details():
    BLURBS = {x['href'].rstrip('/').split('/')[-1]: x['text'] for x in A.services()}
    for url, src, label, cat in D.detail_pages():
        slug = src.split('/')[-1]
        it = A.k2_item(src, captions=D.CAPTIONS.get(slug), labels=True)
        blocks = OVERRIDES.get(slug, lambda b: b)(it['blocks'])
        c = D.CATS[cat]
        single = c['children'] is None
        parent_label, parent_href = ('Products and Services', D.P) if single else (c['label'], f'{D.P}/{cat}')
        body = [
            S.hero12(parent_label, label, cat, wide=True),
            article_section(blocks, aab_image('services/' + c['img']), c['label'], parent_label, parent_href,
                            None if single else 'Products and Services', None if single else D.P, last=True),
        ]
        desc = plain_text(blocks)
        if len(desc) < 60:                 # picture-only articles: describe the page with its menu label and the category's own blurb
            desc = f'{label} - {c["label"]}. {BLURBS[cat]}'
        write_page(url, label, desc, body, WF['post'], nav=S.nav('products'), footer=S.footer('products'), og_type='article')


def build_news_items():
    order = [n['slug'] for n in D.NEWS]
    for n in D.NEWS:
        slug = n['slug']
        it = A.k2_item('news-n-events/item/' + slug, captions=D.CAPTIONS.get(slug))
        blocks = OVERRIDES.get(slug, lambda b: b)(it['blocks'])
        img = aab_image(f'featured/{slug}.jpg')
        others = [s for s in order if s != slug][:2]
        body = [
            S.hero12('News and Events', n['title'], 'news', wide=True),
            article_section(blocks, img, n['title'], D.news_date(slug), None, 'News & Events', '/news-n-events'),
            related_section('Latest news', [news_card_data(s) for s in others]),
        ]
        write_page(f'/news-n-events/item/{slug}', n['title'], plain_text(blocks), body, WF['post'], nav=S.nav('news'), footer=S.footer('news'), og_type='article',
                   og_image=f'{DOMAIN}/{img}')


# ------------------------------------------------------------------ per-article adjustments of the block model
def _demote_after(marker, to=4, until=None):
    """Headings after the heading `marker` are steps of that section: show them one level smaller."""
    def f(blocks):
        on = False
        for b in blocks:
            if b['t'] == 'h':
                txt = A.plain(b['html'])
                if txt == marker: on = True; continue
                if until and txt == until: on = False
                if on and b['lvl'] == 3: b['lvl'] = to
        return blocks
    return f


OVERRIDES = {
    'pump-repairs': _demote_after('PUMP REPAIR PROCESS'),
}


# ------------------------------------------------------------------ generic section fillers
def gap(section, top=None, bottom=None):
    """Section rhythm.  Every template section brings the paddings it needs next to its neighbours on its own template
    page; where a page here puts two sections together that never meet in the template, the same gap (the template's
    --section-text-gap) is added or dropped so that there is exactly one gap between them.  top/bottom: True adds, False drops."""
    cls = section.get('class', [])
    for side, v in (('pt', top), ('pb', bottom)):
        if v is True: cls.append(f'aab-{side}')
        elif v is False: cls.append(f'aab-{side}-0')
    section['class'] = cls
    return section


def header_block(root, label=None, title=None, para=None):
    """Label + heading (+ optional paragraph) at the top of a section."""
    set_label(root, label)
    h = root.select_one('h2')
    if title is not None and h is not None:
        set_text(h, title)
    if para:
        h['class'] = [c if c != 'fda-gap-off' else 'fda-heading-para-gap' for c in h.get('class', [])]
        if 'fda-heading-para-gap' not in h['class']: h['class'].append('fda-heading-para-gap')
        p = frag(f'<p class="fda-gap-off fda-all-appearance">{esc(para)}</p>')[0]
        if h.get('data-w-id'): p['data-w-id'] = h['data-w-id']
        h.insert_after(p)
    return root


def counter_digits(box, number, suffix=''):
    """Fill one of the template's rolling counters (each digit is a pair of 'trains' that slide into place)."""
    counters = box.select('.fda-counter')
    protos = {}
    for c in counters:
        kind = 'two' if c.select_one('.fda-counter-train.fda-two') is not None else 'one'
        protos.setdefault(kind, c)
    tail = [d for d in box.find_all('div', recursive=False) if 'fda-counter' not in (d.get('class') or [])]
    for c in counters: c.extract()
    for t in tail: t.extract()
    kinds = ['two', 'one'] if 'two' in protos and 'one' in protos else list(protos)
    for i, ch in enumerate(str(number)):
        kind = kinds[i % len(kinds)]
        c = clone(protos[kind])
        d = int(ch)
        trains = c.select('.fda-counter-train')
        if kind == 'two':
            # first train ends on its first digit: count up to it
            seq = [(d - k) % 10 for k in range(len(trains[0].find_all('div', recursive=False)))]
            for el, v in zip(trains[0].find_all('div', recursive=False), seq): set_text(el, str(v))
        else:
            # first train is shown at the start and rolls away; the second train's first digit stays
            a = trains[0].find_all('div', recursive=False)
            for k, el in enumerate(a): set_text(el, str((d + k) % 10))
            b = trains[1].find_all('div', recursive=False)
            set_text(b[0], str(d))
        box.append(c)
    if suffix:
        t = clone(tail[0]) if tail else frag('<div></div>')[0]
        set_text(t, suffix); box.append(t)
    return box


def stats_section(label, title, para, stats):
    """Four white cards with rolling numbers (template: home 'complex' section)."""
    s = sec('home-one.html', 'section.fda-complex-v1')
    head = s.select_one('.fda-heading-card-gap')
    header_block(head, label, title, para)
    wrap = s.select_one('.fda-complex-v1-wrap')
    items = wrap.select('.fda-complex-v1-item-wrap')
    for it, st in zip(items, stats):
        counter_digits(it.select_one('.fda-counter-box'), st['n'])
        set_text(it.select_one('.fda-text-style-h5'), st['label'])
    for it in items[len(stats):]: it.decompose()
    return s


def experts_section(label, title, paras, button, features, image=None, image_alt=''):
    """Text + two highlights + picture (template: home 'experts' section)."""
    s = sec('home-one.html', 'section.fda-experts-v3')
    top = s.select_one('.fda-experts-v3-left-top')
    set_label(top, label)
    set_text(top.select_one('h2'), title)
    p = top.select_one('p')
    set_text(p, paras[0])
    prev = p
    for extra in paras[1:]:
        q = clone(p); set_text(q, extra)
        prev['class'] = [c if c != 'fda-button-para-gap' else 'fda-heading-para-gap' for c in prev['class']]
        prev.insert_after(q); prev = q
    set_button(top.select_one('a.fda-button-main'), button[0], button[1])
    feats = s.select('.fda-experts-v3-left-buttom-main > div')
    for el, f in zip(feats, features):
        set_text(el.select_one('h3'), f['title'])
        set_text(el.select_one('p'), f['text'])
        if f.get('icon'):
            img_set(el.select_one('img'), f['icon'], alt='')
    # the template's "98% customer satisfaction" badge with stock faces has no counterpart on the live site
    badge = s.select_one('.fda-experts-v3-right-small')
    if badge is not None: badge.decompose()
    if image:
        img_set(s.select_one('.fda-experts-v3-right > img'), image[0], alt=image_alt, width=image[1], height=image[2])
    else:
        s.select_one('.fda-experts-v3-right > img')['alt'] = image_alt
    return s


# ------------------------------------------------------------------ HOME
ICONS = {  # line icons from the template's own icon set
    'quality': 'images/69b2a15200bc2cb1d23eb09e_Home-one-secure.svg',
    'tech': 'images/69b2a15200bc2cb1d23eb09f_Home-one-awards.svg',
}


def home_hero(slides, sub):
    h = sec('home-one.html', 'div.fda-hero-v2-wrap')
    left = h.select_one('.fda-hero-v2-left-content')
    set_label(left, sub['label'])
    set_text(left.select_one('h1'), slides[0]['texts'][0])
    set_text(left.select_one('p'), sub['para'])
    b = slides[0]['links'][0]
    set_button(left.select_one('a.fda-button-main'), b[0], b[1])
    # bottom-left block: the template has stock faces + "More than 12K clients reviews"; the live welcome block has
    # the accreditation badge and the phone number in that place
    bottom = h.select_one('.fda-hero-v2-left-buttom')
    bottom['class'] = bottom['class'] + ['aab-hero-bottom']
    pics = bottom.select_one('.fda-hero-v2-left-image')
    pics['class'] = pics['class'] + ['aab-hero-badge']
    faces = pics.find_all('div', recursive=False)
    for d in faces[1:]: d.decompose()
    badge, (bw, bh) = badge_image()
    img_set(faces[0].select_one('img'), badge, alt=sub['badge_alt'], width=bw, height=bh)
    star = bottom.select_one('.fda-hero-v2-star')
    star['class'] = star['class'] + ['aab-hero-call']
    rows = star.find_all('div', recursive=False)
    rows[0]['class'] = ['fda-text-color-white']
    set_text(rows[0], sub['call'][0])
    set_html(rows[1], f'<a class="fda-text-style-h6 fda-text-color-white" href="{sub["call"][2]}">{esc(sub["call"][1])}</a>')
    # card: the heading carries a small pill-shaped picture in front of one of its words (as in the template)
    card = h.select_one('.fda-hero-v2-right-content')
    head = card.select_one('.fda-text-style-h4')
    span = head.select_one('span.fda-home-two-left')
    words = slides[2]['texts'][0].split(' ')
    cut = sub.get('pill_word', max(1, len(words) - 3))
    head.clear()
    head.append(NavigableString(' '.join(words[:cut]) + ' '))
    set_text(span, words[cut])
    head.append(span)
    head.append(NavigableString(' ' + ' '.join(words[cut + 1:])))
    set_text(card.select_one('p'), sub['card_para'])
    # no "Watch video" control in the card: the background video simply plays.  The template's no-script fallback
    # picture for that video sat next to the control; it goes back next to the video itself, where Webflow puts it.
    play = card.select_one('.fda-hero-v2-right-bottom')
    fallback = play.select_one('noscript')
    if fallback is not None:
        h.select_one('.fda-hero-v2.w-background-video > video').insert_after(fallback.extract())
    play.decompose()
    return h


def logo_box(w, h, area=9000, max_w=240, max_h=64):
    """Display size that gives logos of very different proportions a similar visual weight (never larger than the file)."""
    import math
    r = w / h
    dw = math.sqrt(area * r); dh = dw / r
    k = min(1, max_w / dw, max_h / dh, w / dw, h / dh)
    return round(dw * k), round(dh * k)


def client_logos(logos):
    from PIL import Image
    out = []
    for lg in logos:
        name = os.path.basename(lg['src'])
        with Image.open(f'{SRC_IMG}/clients/{name}') as im: w, h = im.size
        out.append({'src': aab_image('clients/' + name), 'alt': client_name(lg), 'w': w, 'h': h, 'box': logo_box(w, h)})
    return out


def marquee_clients(logos):
    """Logo strip under the hero (template: home 'marquee').  The strip scrolls one group width per loop, so the
    loop time is scaled with the number of logos in build.py to keep the template's pace."""
    s = sec('home-one.html', 'section.fda-marquee-main-line')
    groups = s.select('.fda-marquee-v1-ten')
    proto = groups[0].select_one('.fda-marquee-v1-item')
    for g in groups:
        g.clear()
        for lg in client_logos(logos):
            it = clone(proto)
            it['class'] = it['class'] + ['aab-client-item']
            img = it.select_one('img')
            img_set(img, lg['src'], alt=lg['alt'], width=lg['w'], height=lg['h'])
            img['class'] = ['aab-client-logo']
            img['style'] = f'--aab-w: {lg["box"][0]}px; --aab-h: {lg["box"][1]}px'
            img['loading'] = 'lazy'
            g.append(it)
    return s


def marquee_group_width(logos, pad=160):
    """Width of one logo group at desktop size (logo + the template's 5rem side paddings)."""
    return sum(lg['box'][0] + pad for lg in client_logos(logos))


CLIENT_NAMES = {'BINA_logo.png': 'BINA', 'brunei-metanol.jpg': 'Brunei Methanol', 'Brunei_LNG_logo.png': 'Brunei LNG', 'BSP_logo.png': 'BSP',
                'gerbaru_jaya_logo.png': 'Gerbaru Jaya', 'Halliburton-Sperry-Drilling_1.png': 'Halliburton Sperry Drilling', 'KMST_Logo.jpg': 'KMST',
                'LANDMARK_Group_logo.png': 'LANDMARK Group', 'north_jaya_logo.png': 'North Jaya', 'swago_logo.png': 'Swago', 'Zetta_group_logo.png': 'Zetta Group'}


def client_name(lg):
    """alt text: the live site's own alt ('BSP logo'), tidied only in letter case"""
    return (lg.get('alt') or '').strip() or CLIENT_NAMES.get(os.path.basename(lg['src']), '')


def credentials_section(label, title, items, pictures=None):
    """Four columns over a picture, text shown on hover (template: service-two 'exterior' section).
    pictures: template pictures for the columns one..four (the first one sets the height of the band)."""
    s = sec('service-two.html', 'div.fda-exterior-wrap')
    if pictures:
        for key, name in zip(('fda-one', 'fda-two', 'fda-three', 'fda-four'), pictures):
            img = s.select_one(f'.fda-exterior-image-main img.{key}')
            keep = {k: img.get(k) for k in ('width', 'height')}
            use_tpl_img(img, name, alt='', sizes='100vw')
            for k, v in keep.items():
                if v: img[k] = v
    head = s.select_one('.fda-exterior-image-top')
    set_label(head, label)
    set_text(head.select_one('h2'), title)
    cols = s.select('.fda-exterior-text-item')
    for col, it in zip(cols, items):
        for t in col.select('.fda-text-style-h5'): set_text(t, it['title'])
        set_text(col.select_one('.fda-exterior-big-paragraph p'), it['text'])
        for im in col.select('img'): im['alt'] = ''
    for im in s.select('.fda-exterior-image-main img'): im['alt'] = ''
    return s


def solutions_section(label, title, cards, button_label, three_cols=False):
    """Picture cards that flip to icon + title + text + button (template: home 'solutions' section)."""
    s = sec('home-one.html', 'section.fda-solutions-v4')
    head = s.select_one('.fda-solutions-v4-top')
    set_label(head, label)
    set_text(head.select_one('h2'), title)
    grid = s.select_one('.fda-solutions-v4-content')
    protos = grid.select('.fda-solutions-v4-item')
    for p in protos: p.extract()
    if three_cols:
        grid['class'] = grid.get('class', []) + ['aab-cols-3']
    # the template shows exactly one card opened (its second); further cards repeat the closed ones
    opened = [k for k, p in enumerate(protos) if 'opacity: 0' in (p.select_one('.fda-solutions-v4-item-over').get('style') or '')]
    closed = [k for k in range(len(protos)) if k not in opened]
    # every card starts on its picture; js/aab.js opens them one by one as the page scrolls (the template's hover is
    # removed, patch 4 in build.py), so the template's opened card starts closed like the others
    shut_plus = protos[closed[0]].select_one('.fda-faq-plus.fda-home-v1')['style']
    for i, c in enumerate(cards):
        it = clone(protos[i] if i < len(protos) else protos[closed[(i - len(protos)) % len(closed)]])
        it.select_one('.fda-solutions-v4-item-over')['style'] = 'opacity: 1'
        it.select_one('.fda-faq-plus.fda-home-v1')['style'] = shut_plus
        set_text(it.select_one('.fda-text-style-h5'), c['title'])
        set_text(it.select_one('.fda-solutions-v4-item-top > .fda-text-color-black'), c['text'])
        set_button(it.select_one('a.fda-button-main'), button_label, c['href'])
        over = it.select_one('.fda-solutions-v4-item-over')
        img = over.select_one('img')
        img_set(img, c['img'], alt=c['title'], width=c.get('w'), height=c.get('h'))
        if c.get('pos'): img['style'] = f'object-position: {c["pos"]}'
        elif img.has_attr('style'): del img['style']
        img['loading'] = 'lazy'
        grid.append(it)
    return s


def links_section(label, title, para, rows, images=None):
    """Picture + rows of links (template: home 'about' section)."""
    s = sec('home-one.html', 'section.fda-about-v1')
    head = s.select_one('.fda-about-v6-top')
    header_block(head, label, title, para)
    box = s.select_one('.fda-about-v1-left-content')
    protos = box.select('a.fda-about-v1-left-item')
    for p in protos: p.extract()
    # start from an inactive row so no row looks pre-selected; rows reuse the template's four row interactions in turn
    for i, (text, href) in enumerate(rows):
        a = clone(protos[i % len(protos)])
        a['href'] = href
        set_text(a.select_one('h3'), text)
        box.append(a)
    if images:
        for img, name in zip(s.select('.fda-about-v6-right img'), images):
            use_tpl_img(img, name, alt='', sizes='(max-width: 767px) 100vw, 50vw')
    return s


def news_section(label, title, button, slugs):
    """Three latest posts (template: home 'blog' section)."""
    s = sec('home-one.html', 'section.fda-blog-v2')
    top = s.select_one('.fda-blog-v2-top')
    set_label(top, label)
    set_text(top.select_one('h2'), title)
    set_button(top.select_one('a.fda-button-main'), button[0], button[1])
    items = s.select('.w-dyn-item')
    for it, slug in zip(items, slugs):
        c = news_card_data(slug)
        a = it.select_one('a')
        a['href'] = c['href']
        card_picture(a.select_one('img'), c)
        d = a.select_one('.fda-discernibale-text div')
        if d is not None: set_text(d, c['title'])
        set_text(it.select_one('.fda-blog-v1-publish-date').find_all('div', recursive=False)[-1], D.news_date(slug, long=True))
        t = it.select_one('.fda-text-style-h5')
        set_text(t, c['title'])
        if t.parent.name == 'a':
            t.parent['href'] = c['href']
        else:                                   # the template's middle card title is not linked; make it a link like the other two
            a2 = frag(f'<a class="w-inline-block" href="{c["href"]}"></a>')[0]
            t.replace_with(a2); a2.append(t)
    return s


def certificates_section(certs, label=None, title=None):
    """Portrait cards with a caption on a dark fade (template: about-two 'team' section); each card opens the full scan."""
    s = sec('about-two.html', 'section.fda-team-v1')
    head = s.select_one('.fda-team-v1-top')
    if title:
        set_label(head, label)
        set_text(head.select_one('h2'), title)
    else:
        head.decompose()
    grid = s.select_one('.fda-team-content')
    items = grid.select('.w-dyn-item')
    proto = items[0]
    for it in items: it.extract()
    for c in certs:
        it = clone(proto)
        full = aab_image(c['img'])                                        # the scan as published on the live site
        thumb, (w, hh) = certificate_card_image(c['img'], c['file'])
        for a in it.select('a.fda-team-item-link, a.fda-team-item-text-left'):
            a['href'] = ASSET + full; a['aria-label'] = c['alt']; a['target'] = '_blank'; a['rel'] = 'noopener'
        img = it.select_one('a.fda-team-item-link img')
        style = img.get('style')
        img_set(img, thumb, alt=c['alt'], width=w, height=hh)
        if style: img['style'] = style
        img['loading'] = 'lazy'
        lines = it.select('a.fda-team-item-text-left > div')
        set_text(lines[0], c['title']); set_text(lines[1], c['sub'])
        it.select_one('.fda-team-item-icon-wrapper').decompose()          # social icons: not applicable
        card = it.select_one('.fda-team-item')
        card['class'] = card['class'] + ['aab-cert']
        grid.append(it)
    return s


def build_home():
    h = A.home(); slides = A.slides(); ab = A.about()
    w = h['welcome']
    hero = home_hero(slides, {'label': w['title'], 'para': w['sub'], 'card_para': [x for x in h['services'] if 'Engineering' in x['title']][0]['text'],
                              'call': w['call'], 'badge_alt': w['iso_badge_alt'], 'pill_word': 5})
    # live copy: "Advance Automation Sdn Bhd. was established in 2010. It was the brainchild ..." -> heading + paragraph (as on the About page)
    first = ab['sub']
    assert w['paras'][0].startswith(first + '. ')
    intro = experts_section('About us', first, [w['paras'][0][len(first) + 2:], w['paras'][1]], w['button'],
                            [dict(h['why']['items'][0], icon=ICONS['quality']), dict(h['why']['items'][1], icon=ICONS['tech'])],
                            image_alt=S.COMPANY)
    creds = credentials_section(S.ISO_LINE, ab['paras'][1].rstrip('.'), h['credentials'], D.CREDENTIAL_PICTURES)
    certs = certificates_section(D.CERTIFICATES)
    pos = {'services1.jpg': '63% 50%', 'services3.jpg': '55% 50%'}
    cards = [{'title': x['title'], 'text': x['text'], 'href': x['href'], 'img': aab_image('services/' + os.path.basename(x['img'])), 'w': 1280, 'h': 700,
              'pos': pos.get(os.path.basename(x['img']))} for x in h['services']]
    services = solutions_section(h['services_title'], slides[1]['texts'][0], cards, 'Read more', three_cols=True)
    wd = h['what_we_do']
    tag_links = {'Engineering and Services': f'{D.P}/engineering-and-services', 'Calibration & Certification': f'{D.P}/calibration-certification-services',
                 'Pump & Rotating Equipments': f'{D.P}/engineering-and-services', 'Flame Arresters & Tank Accessories': f'{D.P}/control-and-instrument-valves'}
    what = links_section(None, wd['title'], wd['text'], [(t, tag_links.get(t, D.P)) for t in wd['tags']])
    stats = stats_section(None, ab['leader']['title'], ab['leader']['text'], h['stats'])
    news = news_section(None, h['latest_title'], ('News and Events', '/news-n-events'), h['latest'])
    clients = marquee_clients(A.clients()['logos'])
    # rhythm: exactly one gap between neighbours (see gap())
    gap(intro, bottom=False)            # the credentials block brings its own top gap
    gap(certs, bottom=False)            # followed by "Our services", which gets the gap on top
    gap(services, top=True)
    gap(stats, bottom=False)            # the news block brings its own top gap
    body = [hero, clients, intro, creds, certs, services, what, stats, news]
    # the home page of the template has faint vertical guide lines behind its sections
    lines = sec('home-one.html', 'body > div.fda-home-one-body-line-wrap')
    write_page('/', 'Home', w['paras'][0], body, WF['home'], nav=S.nav('home', 'home-one.html'), footer=S.footer('home'),
               body_class='fda-position-relative', before_nav=[lines], main_class='fda-position-relative fda-z-4',
               scripts=['aab.js'])


# ------------------------------------------------------------------ ABOUT US
def intro_section(label, title, note, para, button, big_image, small_image):
    """Large picture + heading + bracket line + small picture + paragraph + button (template: about-two 'who we are')."""
    s = sec('about-two.html', 'section.fda-about-v3')
    right = s.select_one('.fda-about-v3-right')
    set_label(right, label)
    set_text(right.select_one('h2'), title)
    n = right.select_one('h2').find_next_sibling('p')
    if note: set_text(n, f'[ {note} ]')
    else: n.decompose()
    bottom = s.select_one('.fda-about-v3-right-buttom')
    set_text(bottom.select_one('p'), para)
    if button: set_button(bottom.select_one('a.fda-button-main'), button[0], button[1])
    else:
        bottom.select_one('a.fda-button-main').decompose()
        bottom.select_one('p')['class'] = ['fda-gap-off']
    left = s.select_one('.fda-about-v3-left')
    use_tpl_img(left.select_one('img'), big_image, alt=title, sizes='(max-width: 767px) 100vw, 50vw')
    left['class'] = left['class'] + ['aab-cover']                      # keeps the box in the shape of the template's picture
    si = s.select_one('.fda-about-v3-right-image img')
    if small_image.startswith('images/aab/'): img_set(si, small_image, alt='')
    else: use_tpl_img(si, small_image, alt='', sizes='253px')
    return s


def cards_dark_section(label, title, cards):
    """Bordered cards (icon, title, text) over a dark picture (template: about-two 'expertise' section)."""
    s = sec('about-two.html', 'section.fda-expertise-v2')
    head = s.select_one('.fda-expertise-top-wrapper')
    set_label(head, label)
    set_text(head.select_one('h2'), title)
    wrap = s.select_one('.fda-expertise-v2-wrap')
    protos = wrap.select('.fda-expertise-v2-item')
    for p in protos: p.extract()
    rows = [wrap]
    for r in range(1, (len(cards) + 2) // 3):
        w2 = clone(wrap); wrap.parent.append(w2); rows.append(w2)
    # the template highlights one card (its second) until another one is hovered; further cards repeat the plain ones,
    # each with the icon of its column
    plain = [k for k, p in enumerate(protos) if 'fda-inactive' in p.select_one('.fda-expertise-v2-overlay')['class']]
    icons = [p.select_one('.fda-expertise-v2-item-top img')['src'] for p in protos]
    for i, c in enumerate(cards):
        it = clone(protos[i] if i < len(protos) else protos[plain[(i - len(protos)) % len(plain)]])
        it.select_one('.fda-expertise-v2-item-top img')['src'] = icons[i % len(icons)]
        set_text(it.select_one('.fda-text-style-h5'), c['title'])
        set_text(it.select_one('p'), c['text'])
        it.select_one('img')['alt'] = ''
        rows[i // 3].append(it)
    return s


def build_about():
    ab = A.about()
    roles = ' '.join(ab['roles'])
    lead = f"{ab['lead']} {roles}"
    # the banner right above already carries the company name, so the intro starts with its heading (no label)
    intro = experts_section(None, ab['sub'], [lead, ' '.join(ab['paras'])], (S.CTA_LABEL, '/contact'),
                            [dict(ab['boxes'][0], icon=ICONS['quality']), dict(ab['boxes'][1], icon=ICONS['tech'])], image_alt=S.COMPANY)
    motto = intro_section(ab['motto_title'], ab['motto'][0], S.ISO_LINE, ' '.join(ab['motto'][1:]), ('Products and Services', D.P),
                          'Readiness-service-three', aab_image('about_us/about_us2.jpg'))      # offshore platform (template library)
    services = cards_dark_section('Products and Services', A.slides()[2]['texts'][0], ab['features'])
    stats = stats_section(None, ab['leader']['title'], ab['leader']['text'], ab['stats'])
    gap(intro, bottom=False)            # the motto block brings its own top gap
    gap(motto, bottom=True)             # followed by the dark band
    gap(stats, top=True)                # follows the dark band
    body = [S.hero12(S.COMPANY, 'About us', 'about'), intro, motto, services, stats]
    write_page('/about-us', 'About us', f"{ab['sub']}. {ab['lead']}", body, WF['about'], nav=S.nav('about'), footer=S.footer('about'))


# ------------------------------------------------------------------ PRODUCTS AND SERVICES
def service_cards_section(label, title, cards, button_label):
    """Bordered cards: small picture, title, text, button (template: about-three 'support' section)."""
    s = sec('about-three.html', 'section.fda-support-v1')
    head = s.select_one('.fda-support-v1-top')
    set_label(head, label)
    set_text(head.select_one('h2'), title)
    main = s.select_one('.fda-support-v1-main')
    kids = main.find_all(True, recursive=False)
    protos = [k for k in kids if 'fda-border' in (k.get('class') or [])]
    for k in kids: k.extract()
    main['class'] = main.get('class', []) + ['aab-wrap']
    for i, c in enumerate(cards):
        it = clone(protos[i % len(protos)])
        img_set(it.select_one('img'), c['img'], alt=c['title'], width=c.get('w'), height=c.get('h'))
        set_text(it.select_one('.fda-text-style-h5'), c['title'])
        set_text(it.select_one('p'), c['text'])
        set_button(it.select_one('a.fda-button-main'), button_label, c['href'])
        main.append(it)
    return s


def build_products():
    sv = A.services()
    cards = [{'title': x['title'], 'text': x['text'], 'href': x['href'], 'img': aab_image('services/' + os.path.basename(x['img'])), 'w': 1280, 'h': 700} for x in sv]
    grid = service_cards_section(A.home()['services_title'], A.slides()[1]['texts'][0], cards, 'Read more')
    gap(grid, bottom=True)              # last section of the page
    body = [S.hero12(S.COMPANY, 'Products and Services', 'products'), grid]
    write_page(D.P, 'Products and Services', A.home()['what_we_do']['text'], body, WF['services'], nav=S.nav('products'), footer=S.footer('products'))


def category_section(label, statement, rows, images):
    """Statement + rows of links + two pictures (template: service-one 'capabilities' section)."""
    s = sec('service-one.html', 'section.fda-capabilities-v1')
    left = s.select_one('.fda-capabilities-v1-left')
    left.select_one('.fda-capabilities-v1-left-top').decompose()       # "20+ years of experience": no counterpart for a category
    holder = left.select_one('a.fda-capabilities-v1-left-item').parent
    proto = holder.select_one('a.fda-capabilities-v1-left-item')
    for a in holder.select('a.fda-capabilities-v1-left-item'): a.extract()
    for text, href in rows:
        a = clone(proto); a['href'] = href
        set_text(a.select_one('.fda-text-style-h5'), text)
        a.select_one('img')['alt'] = ''
        holder.append(a)
    right = s.select_one('.fda-capabilities-v1-right')
    set_label(right, label)
    set_text(right.select_one('h2'), statement)
    cells = right.select('.fda-capabilities-v1-right-item')
    for cell, im in zip(cells[:2], images):
        img_set(cell.select_one('img'), im[0], alt=im[1], width=im[2], height=im[3])
        cell['class'] = cell['class'] + ['aab-tile']                   # both pictures in the template's 4:3 tile shape
    cells[2].decompose()                                               # small paragraph: nothing to put there
    right.select_one('.fda-capabilities-v1-right-bottom')['class'] += ['aab-two']
    return s


CAT_SECOND_IMAGE = {  # a second picture for the category page, taken from that category's own articles
    'custom-made': ('products-services/Custom-made_Stud-Bolts/Stud-Bolts-4.jpg', 'Stud Bolts'),
    'safety-products': ('products-services/Safety_Equipment/Shackles-Hooks-1.jpg', 'Shackles and Hooks'),
    'capabilities': ('products-services/Calibration/onsite_calibration_service.jpg', 'Calibration'),
    'engineering-and-services': ('products-services/Engineering/pump-testing-service.jpg', 'Pump testing service'),
}


def build_categories():
    from PIL import Image
    blurbs = {x['href'].rstrip('/').split('/')[-1]: x['text'] for x in A.services()}
    for slug, c in D.CATS.items():
        if c['children'] is None:
            continue
        cat = A.category(slug)
        rows = [(i['title'], i['href']) for i in cat['items']]
        first = (aab_image('services/' + c['img']), c['label'], 1280, 700)
        sub, alt = CAT_SECOND_IMAGE[slug]
        with Image.open(f'{SRC_IMG}/{sub}') as im: w, hh = im.size
        second = (aab_image(sub), alt, w, hh)
        body = [S.hero12('Products and Services', c['label'], slug),
                category_section(None, blurbs[slug], rows, [first, second])]     # no label: it would repeat the banner title
        write_page(f'{D.P}/{slug}', c['label'], blurbs[slug], body, WF['category'], nav=S.nav('products'), footer=S.footer('products'))


# ------------------------------------------------------------------ CLIENTS
def build_clients():
    from PIL import Image
    cl = A.clients()
    s = sec('home-one.html', 'section.fda-complex-v1')
    head = s.select_one('.fda-heading-card-gap')
    set_label(head, None)
    set_text(head.select_one('h2'), cl['title'])
    wrap = s.select_one('.fda-complex-v1-wrap')
    proto = wrap.select_one('.fda-complex-v1-item-wrap')
    for it in wrap.select('.fda-complex-v1-item-wrap'): it.extract()
    for lg in cl['logos']:
        it = clone(proto)
        inner = it.select_one('.fda-complex-v1-item')
        inner.clear()
        f = f'{SRC_IMG}/clients/{os.path.basename(lg["src"])}'
        with Image.open(f) as im: w, hh = im.size
        inner['class'] = inner.get('class', []) + ['aab-client-tile']
        inner.append(frag(f'<img alt="{html.escape(client_name(lg), quote=True)}" class="aab-client-logo" height="{hh}" loading="lazy" src="{ASSET}{aab_image("clients/" + os.path.basename(lg["src"]))}" width="{w}" />')[0])
        wrap.append(it)
    gap(s, top=True)                    # first section under the banner
    body = [S.hero12(S.COMPANY, 'Clients', 'clients'), s]
    names = ', '.join(CLIENT_NAMES[os.path.basename(lg['src'])] for lg in cl['logos'])
    write_page('/clients', 'Clients', f'{cl["title"]} - {S.COMPANY}: {names}.', body, WF['home'], nav=S.nav('clients'), footer=S.footer('clients'))


# ------------------------------------------------------------------ NEWS AND EVENTS
def build_newslist():
    s = sec('blog.html', 'section.fda-blog-v1')
    head = s.select_one('.fda-blog-heading-wrap')
    set_label(head, None)                                              # the banner right above already says "News and Events"
    set_text(head.select_one('h2'), A.home()['latest_title'])
    grid = s.select_one('.fda-blog-v1-content')
    proto = grid.select_one('.w-dyn-item')
    for it in grid.select('.w-dyn-item'): it.extract()
    for n in D.NEWS:
        c = news_card_data(n['slug'])
        it = clone(proto)
        a = it.select_one('a.fda-blog-v1-item-image'); a['href'] = c['href']
        card_picture(a.select_one('img'), c)
        set_text(it.select_one('.fda-blog-v1-publish-date').find_all('div', recursive=False)[-1], c['date'])
        t = it.select_one('a.fda-text-style-h4'); t['href'] = c['href']; set_text(t, c['title'])
        t['aria-label'] = c['title']
        set_button(it.select_one('a.fda-button-main'), 'Read more', c['href'])
        grid.append(it)
    pg = s.select_one('.w-pagination-wrapper')
    if pg is not None: pg.decompose()                                  # all eight items fit on one page
    body = [S.hero12(S.COMPANY, 'News and Events', 'news'), s]
    write_page('/news-n-events', 'News and Events', ' '.join(n['intro'] for n in D.NEWS[:2]), body, WF['blog'], nav=S.nav('news'), footer=S.footer('news'))


# ------------------------------------------------------------------ CONTACT
def build_contact():
    ct = A.contact()
    s1 = sec('contact.html', 'section.fda-contact-v1')
    set_label(s1.select_one('.fda-contact-v1-heading'), None)
    set_text(s1.select_one('.fda-contact-v1-heading h2'), ct['title'])
    right = s1.select_one('.fda-contact-v1-right')
    set_text(right.select_one('p'), ct['lead'])
    set_text(right.select_one('h3'), 'Get in touch')
    items = right.select('.fda-contact-v1-item')
    # e-mail
    set_text(items[0].select_one('.fda-text-style-h6'), 'Send mail @')
    a = items[0].select_one('a'); a['href'] = 'mailto:' + S.EMAIL; set_text(a, S.EMAIL)
    # phone
    set_text(items[1].select_one('.fda-text-style-h6'), 'Call us')
    a = items[1].select_one('a'); proto = a; holder = a.parent
    a.extract()
    line = frag('<div class="fda-text-color-white"></div>')[0]
    line.append(NavigableString('Tel: '))
    for i, (num, tel) in enumerate(S.PHONES):
        b = clone(proto); b['href'] = 'tel:' + tel; set_text(b, num)
        if i: line.append(NavigableString(' / '))
        line.append(b)
    holder.append(line)
    holder.append(frag(f'<div class="fda-text-color-white">Fax: {S.FAX}</div>')[0])
    # address
    set_text(items[2].select_one('.fda-text-style-h6'), 'Address')
    set_html(items[2].select('.fda-contact-v1-item-text > div')[-1], '<br />'.join(esc(x) for x in S.ADDRESS))
    # working hours: one more row of the same kind (the live site shows them in its footer)
    hrs = clone(items[2])
    icon = hrs.select_one('img')
    img_set(icon, 'images/69b2a15200bc2cb1d23ead8e_Caleander-blog.svg', alt='', width=24, height=24)
    icon['class'] = ['fda-invert']
    set_text(hrs.select_one('.fda-text-style-h6'), 'Working hours')
    set_html(hrs.select('.fda-contact-v1-item-text > div')[-1], '<br />'.join(esc(f'{d}: {", ".join(t)}') for d, t in S.HOURS))
    items[2].insert_after(hrs)
    for im in right.select('.fda-contact-v1-item img'): im['alt'] = ''
    bottom = right.select_one('.fda-contact-v1-bottom')
    bottom.decompose()                                                 # social icons: the live site has no social accounts
    s1.select_one('.fda-contact-v1-left img')['alt'] = S.COMPANY
    wrap = s1.select_one('.fda-contact-v1-content')
    wrap['class'] = wrap['class'] + ['aab-stretch']                     # the details card is longer than in the template; the picture follows it
    # form
    s2 = sec('contact.html', 'section.fda-contact-v2')
    set_label(s2.select_one('.fda-contact-v1-heading'), None)
    set_text(s2.select_one('.fda-contact-v1-heading h2'), 'Send us a message')
    form = s2.select_one('form')
    form['name'] = 'wf-form-Contact'; form['data-name'] = 'Contact'; form['id'] = 'wf-form-Contact'; form['aria-label'] = 'Contact'
    # Without an action the template's script would post the visitor's message to webflow.com under the template's site id.
    # Until the site has its own form handler, the form hands the message to the visitor's mail program instead
    # (replace the three attributes below with the handler's URL / method when there is one).
    form['action'] = 'mailto:' + S.EMAIL; form['method'] = 'post'; form['enctype'] = 'text/plain'
    inputs = form.select('input.fda-input')
    ta = form.select_one('textarea')
    proto = inputs[0]
    for i in inputs: i.extract()
    defs = [('Name', 'text', 'name', True), ('Company', 'text', 'company', False), ('E-mail', 'email', 'email', True), ('Contact No', 'tel', 'contact-no', True), ('Subject', 'text', 'subject', True)]
    for label, typ, name, req in reversed(defs):
        i = clone(proto)
        i['class'] = ['fda-input', 'w-input'] + (['aab-span-2'] if name == 'subject' else [])
        i['name'] = label; i['data-name'] = label; i['id'] = name; i['type'] = typ       # name = the live site's field label (it is what the recipient reads)
        i['placeholder'] = label + ('*' if req else '')
        i['maxlength'] = '256'
        if req: i['required'] = ''
        elif i.has_attr('required'): del i['required']
        form.insert(0, i)
    ta['placeholder'] = 'Message*'; ta['required'] = ''; ta['name'] = 'Message'; ta['data-name'] = 'Message'      # id stays 'Message': the template's two-column rule is tied to it
    # the real submit control lies invisibly over the drawn button (empty value, as in the template); it gets its name for screen readers
    sub = form.select_one('input.fda-submit'); sub['value'] = ''; sub['aria-label'] = ct['submit']
    for t in form.select('.fda-button-text-1, .fda-button-text-2'): set_text(t, ct['submit'])
    body = [S.hero12(S.COMPANY, 'Contact', 'contact'), s1, s2]
    write_page('/contact', 'Contact', ct['lead'], body, WF['contact'], chunk='forms', nav=S.nav('contact'), footer=S.footer('contact'))


# ------------------------------------------------------------------ 404
def build_notfound():
    n = S.nav(None, '404.html')
    u = sec('404.html', 'div.fda-utility-page-wrap')
    u.select_one('a.fda-button-main')['href'] = '/'                     # "Back to home"
    f = S.footer(None)
    doc_path = write_page('/404', 'Page not found', 'Page not found', [u], WF['404'], nav=n, footer=f)
    # keep it as /404.html at the site root (what static hosts look for).  A host serves this file for any missing URL,
    # at any depth, so its asset paths are absolute from the site root.
    s = open(doc_path, encoding='utf-8').read().replace('"../', '"/').replace('url(../', 'url(/').replace(' ../', ' /')
    # an error page has no address of its own and should stay out of search results
    s = re.sub(r'<meta content="[^"]*/404" property="og:url" />\n', '', s)
    s, k = re.subn(r'<link href="[^"]*/404" rel="canonical" />', '<meta content="noindex" name="robots" />', s)
    assert k == 1
    open(f'{OUT}/404.html', 'w', encoding='utf-8').write(s)
    shutil.rmtree(os.path.dirname(doc_path))
    PAGES[-1]['file'] = '404.html'; PAGES[-1]['url'] = '/404.html'
