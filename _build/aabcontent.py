"""Read the scraped Advance Automation pages (source-site/pages) and turn each page's own content into a small,
template-neutral block model.  Nothing is written or invented here: every string and image comes from the scrape.

Block model (list of dicts)
    {'t': 'h', 'lvl': 2|3|4, 'html': inline}
    {'t': 'p', 'html': inline}
    {'t': 'ul'|'ol', 'items': [{'html': inline, 'sub': [blocks]}], 'cols': 1|2|3, 'kind': 'label'|'text'}
    {'t': 'figs', 'figs': [{'src', 'alt', 'w', 'h', 'cap'}]}
"""
import os, re, html, glob, copy
from bs4 import BeautifulSoup, NavigableString, Tag, Comment
from PIL import Image
import client_changes as CC

SRC = (os.environ.get('AAB_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/source-site'
MISSING_IMAGES = []          # (page, src) of images that are 404 on the live site
_soups = {}


def soup(rel):
    """rel = path below source-site/pages without .html, e.g. 'about-us'."""
    if rel not in _soups:
        p = f'{SRC}/pages/{rel}.html'
        _soups[rel] = BeautifulSoup(raw(rel), 'html5lib')
    return _soups[rel]


def raw(rel):
    """The scraped page with the changes the client asked for applied (client_changes.py)."""
    return CC.apply(rel, open(f'{SRC}/pages/{rel}.html', encoding='utf-8').read())


# ---------------------------------------------------------------- text helpers
def ws(s):
    return re.sub(r'[ \t\r\n\xa0]+', ' ', s or '')


def text_of(el):
    return ws(el.get_text(' ')).strip() if el is not None else ''


def words(s):
    return len(re.findall(r'\w[\w\'’./&-]*', s))


def is_upper(s):
    letters = [c for c in s if c.isalpha()]
    return bool(letters) and sum(c.isupper() for c in letters) / len(letters) > 0.9


# ---------------------------------------------------------------- e-mail cloaks
def cloak_emails(rel):
    """Joomla hides e-mail addresses behind a small script.  Return {span id: address}."""
    out = {}
    h = raw(rel)
    for m in re.finditer(r'var addy_text([0-9a-f]+)\s*=\s*((?:"[^"]*"\s*\+?\s*)+);', h):
        parts = re.findall(r'"([^"]*)"', m.group(2))
        out['cloak' + m.group(1)] = html.unescape(''.join(parts))
    return out


# ---------------------------------------------------------------- images
def local_image(src):
    """Map a live image URL to the scraped file (source-site/images/...) -> (site path, abs file) or None."""
    s = src.strip()
    s = re.sub(r'^https?://(www\.)?advanceautomationbrunei\.com', '', s)
    m = re.match(r'^/images/aab/(.+)$', s)
    if not m:
        return None
    sub = m.group(1)
    f = f'{SRC}/images/{sub}'
    if not os.path.isfile(f):
        return None
    return 'images/aab/' + sub, f


def fig_from_img(img, page):
    src = img.get('src', '')
    loc = local_image(src)
    if not loc:
        MISSING_IMAGES.append((page, src))
        return None
    site_path, f = loc
    with Image.open(f) as im:
        nw, nh = im.size
    def num(v):
        try: return int(float(re.sub(r'[^0-9.]', '', str(v))))
        except Exception: return None
    aw = num(img.get('width'))
    st = img.get('style', '') or ''
    m = re.search(r'(?<![-\w])width:\s*([0-9.]+)px', st)
    if m: aw = int(float(m.group(1)))
    # shown size on the live site = width attribute (never larger than the file itself)
    w = min(aw, nw) if aw else nw
    hgt = round(nh * w / nw)
    alt = ws(img.get('alt') or '').strip()
    return {'src': site_path, 'file': f, 'alt': alt, 'w': w, 'h': hgt, 'nw': nw, 'nh': nh, 'cap': None}


# ---------------------------------------------------------------- inline html
ALLOWED_INLINE = {'strong': 'strong', 'b': 'strong', 'em': 'em', 'i': 'em', 'a': 'a', 'br': 'br', 'sup': 'sup', 'sub': 'sub'}


def inline_html(node, ctx):
    """Serialise the inline content of node, keeping only strong/em/a/br."""
    out = []
    for c in node.children:
        if isinstance(c, Comment):
            continue
        if isinstance(c, NavigableString):
            out.append(html.escape(ws(str(c)), quote=False))
            continue
        n = c.name
        if n in ('script', 'style', 'img'):
            continue
        if n == 'span' and (c.get('id') or '').startswith('cloak'):
            addr = ctx['emails'].get(c.get('id'))
            if addr:
                out.append(f'<a href="mailto:{addr}">{addr}</a>')
            continue
        inner = inline_html(c, ctx)
        if n == 'br':
            out.append('<br />')
        elif n in ALLOWED_INLINE:
            tag = ALLOWED_INLINE[n]
            if tag == 'a':
                href = (c.get('href') or '').strip()
                if not href or href.startswith('#') or not inner.strip():
                    out.append(inner)
                else:
                    ext = ' target="_blank" rel="noopener"' if href.startswith('http') and 'advanceautomationbrunei.com' not in href else ''
                    out.append(f'<a href="{html.escape(href)}"{ext}>{inner}</a>')
            elif inner.strip():
                # keep spaces and line breaks outside the tag so "<strong>Label </strong>text" stays readable
                parts = []
                for part in inner.split('<br />'):
                    lead = ' ' if part[:1] == ' ' else ''
                    trail = ' ' if part[-1:] == ' ' else ''
                    parts.append(f'{lead}<{tag}>{part.strip()}</{tag}>{trail}' if part.strip() else '')
                out.append('<br />'.join(parts))
            else:
                out.append(inner)
        else:
            out.append(inner)
    s = ''.join(out)
    s = re.sub(r' +', ' ', s)
    return s


def clean_inline(s):
    s = re.sub(r'^(\s|<br />)+|(\s|<br />)+$', '', s)
    s = re.sub(r'\s*<br />\s*', '<br />', s)
    s = re.sub(r'(<br />){2,}', '<br />', s)
    s = re.sub(r'<(strong|em)>\s*</\1>', '', s)
    s = re.sub(r'</strong>(\s*)<strong>', r'\1', s)
    return s.strip()


def plain(s):
    return ws(html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


# ---------------------------------------------------------------- block walker
BLOCK_TAGS = {'p', 'ul', 'ol', 'table', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote'}


def has_block_children(el):
    return any(isinstance(c, Tag) and c.name in BLOCK_TAGS for c in el.descendants)


INLINE_TAGS = {'img', 'br', 'span', 'strong', 'b', 'em', 'i', 'a', 'sup', 'sub', 'u', 'font', 'small'}


def walk(node, ctx, out):
    run = []                      # consecutive inline nodes = one implicit paragraph
    def flush():
        if run:
            paragraph_nodes(run[:], ctx, out); run.clear()
    for c in list(node.children):
        if isinstance(c, Comment):
            continue
        if isinstance(c, NavigableString):
            if ws(str(c)).strip() or run:
                run.append(c)
            continue
        n = c.name
        if n in ('script', 'style', 'hr'):
            continue
        if n in INLINE_TAGS and not has_block_children(c):
            run.append(c)
            continue
        flush()
        if n in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            t = clean_inline(inline_html(c, ctx))
            t = re.sub(r'</?strong>', '', t)
            if plain(t):
                out.append({'t': 'h', 'lvl': 2 if c.find('span', class_='title-left') is not None else 3, 'html': t, 'src': n})
        elif n == 'p':
            paragraph_nodes(list(c.children), ctx, out)
        elif n in ('ul', 'ol'):
            out.append(make_list(c, ctx))
        elif n == 'table':
            table(c, ctx, out)
        else:                     # div, blockquote, ...
            walk(c, ctx, out)
    flush()


def _frag(nodes, ctx):
    """inline html of a list of sibling nodes"""
    holder = BeautifulSoup('<div></div>', 'html5lib').div
    for n in nodes:
        holder.append(copy.copy(n))
    return inline_html(holder, ctx)


def strong_only(line):
    rest = re.sub(r'<strong>.*?</strong>', '', line, flags=re.S)
    return bool(plain(line)) and not plain(rest)


def emit_text(t, out):
    """t = inline html of one source paragraph.  Two line breaks in a row separate paragraphs; a line that is
    bold from start to end is a heading (ALL CAPS = section heading, otherwise sub-heading)."""
    t = re.sub(r'\s*<br />\s*', '<br />', t)
    t = re.sub(r'</strong>(\s*)<strong>', r'\1', t)
    for para in re.split(r'(?:<br />){2,}', t):
        lines = [x for x in (clean_inline(y) for y in para.split('<br />')) if plain(x)]
        if not lines:
            continue
        if all(strong_only(ln) and words(plain(ln)) <= 16 for ln in lines):
            for ln in lines:
                h = re.sub(r'</?strong>', '', ln)
                out.append({'t': 'h', 'lvl': 3 if is_upper(plain(h)) else 4, 'html': h, 'src': 'strong'})
        else:
            out.append({'t': 'p', 'html': '<br />'.join(lines)})


def paragraph_nodes(nodes, ctx, out):
    """One paragraph worth of inline nodes: text, pictures, or both (kept in their original order).
    Pictures separated by a line break become separate rows."""
    has_img = any(isinstance(n, Tag) and (n.name == 'img' or n.find('img') is not None) for n in nodes)
    if not has_img:
        emit_text(_frag(nodes, ctx), out)
        return
    buf, figs = [], []
    def flush_figs():
        if figs:
            out.append({'t': 'figs', 'figs': figs[:]}); figs.clear()
    def flush_text():
        t = ''.join(buf); buf.clear()
        if plain(t):
            flush_figs()
            emit_text(t, out)
    def rec(node_list, wrap=None):
        for c in node_list:
            if isinstance(c, Comment): continue
            if isinstance(c, NavigableString):
                s = html.escape(ws(str(c)), quote=False)
                buf.append(f'<{wrap}>{s}</{wrap}>' if wrap and s.strip() else s)
            elif c.name == 'img':
                flush_text()
                f = fig_from_img(c, ctx['page'])
                if f: figs.append(f)
            elif c.name == 'br':
                if plain(''.join(buf)) or not figs: buf.append('<br />')
                else: flush_figs()                      # a line break between pictures starts a new row
            elif c.name in ('script', 'style'):
                continue
            elif c.name == 'span' and (c.get('id') or '').startswith('cloak'):
                addr = ctx['emails'].get(c.get('id'))
                if addr: buf.append(f'<a href="mailto:{addr}">{addr}</a>')
            elif c.find('img') is not None:
                rec(list(c.children), 'strong' if c.name in ('strong', 'b') else wrap)
            else:
                frag = inline_html(c, ctx)
                tag = ALLOWED_INLINE.get(c.name)
                if tag == 'a' and c.get('href'):
                    buf.append(f'<a href="{html.escape(c.get("href"))}">{frag}</a>')
                elif tag in ('strong', 'em') and frag.strip():
                    buf.append(f'<{tag}>{frag.strip()}</{tag}>')
                else:
                    buf.append(frag)
    rec(nodes)
    flush_text()
    flush_figs()


def make_list(ul, ctx):
    items = []
    for li in ul.find_all('li', recursive=False):
        sub = []
        # inline part = everything except nested lists
        clone = copy.copy(li)
        for nested in clone.find_all(['ul', 'ol']):
            nested.extract()
        t = clean_inline(inline_html(clone, ctx))
        for nested in li.find_all(['ul', 'ol'], recursive=False):
            sub.append(make_list(nested, ctx))
        for nested_p in li.find_all('p', recursive=False):
            for nl in nested_p.find_all(['ul', 'ol'], recursive=False):
                sub.append(make_list(nl, ctx))
        if plain(t) or sub:
            items.append({'html': t, 'sub': sub})
    # lists nested directly inside the list (invalid but common in old editors)
    for nested in ul.find_all(['ul', 'ol'], recursive=False):
        sub = make_list(nested, ctx)
        if items: items[-1]['sub'].append(sub)
        else: items.extend(sub['items'])
    return {'t': ul.name, 'items': items, 'cols': 1, 'kind': None}


def cell_is_simple(td):
    if td.find(['img', 'ul', 'ol', 'table']) is not None:
        return False
    return words(text_of(td)) <= 14


def cell_lines(td, ctx):
    """The text lines of a cell (one per <p>, split again at <br>)."""
    sub = []
    walk(td, ctx, sub)
    lines = []
    for b in sub:
        if b['t'] in ('p', 'h'):
            lines.extend(x for x in (clean_inline(y) for y in b['html'].split('<br />')) if plain(x))
    return lines


def table(tb, ctx, out):
    rows = []
    body = tb.find('tbody', recursive=False) or tb
    for tr in body.find_all('tr', recursive=False):
        cells = tr.find_all(['td', 'th'], recursive=False)
        if cells: rows.append(cells)
    if not rows:
        return
    ncols = max(len(r) for r in rows)
    flat = [td for r in rows for td in r]
    textual = all(td.find(['img', 'ul', 'ol', 'table']) is None for td in flat)
    # key/value table: two columns, the first one being short labels that end with ':'
    if textual and ncols == 2 and len(rows) >= 2 and all(text_of(r[0]).endswith(':') and words(text_of(r[0])) <= 5 for r in rows if text_of(r[0])):
        items = []
        for r in rows:
            k = clean_inline(inline_html(r[0], ctx)); v = clean_inline(inline_html(r[1], ctx)) if len(r) > 1 else ''
            k = re.sub(r'</?strong>', '', k)
            if plain(k) or plain(v):
                items.append({'html': f'<strong>{k}</strong> {v}'.strip(), 'sub': []})
        out.append({'t': 'ul', 'items': items, 'cols': 1, 'kind': 'text', 'from': 'table-kv'})
        return
    # a table that is really a list laid out in columns: every cell holds nothing but short lines
    if textual:
        grid = [[cell_lines(td, ctx) for td in r] for r in rows]
        lines_all = [ln for r in grid for c in r for ln in c]
        if len(lines_all) >= 3 and all(words(plain(ln)) <= 12 for ln in lines_all):
            many_lines = any(len(c) > 1 for r in grid for c in r)
            if many_lines:
                # each cell holds a column of lines -> read line by line across the columns (row order)
                cols_ = [[ln for r in grid if ci < len(r) for ln in r[ci]] for ci in range(ncols)]
                cols_ = [c for c in cols_ if c]
                seq = [c[i] for i in range(max(len(c) for c in cols_)) for c in cols_ if i < len(c)]
                ncols = len(cols_)
            else:
                seq = [c[0] for r in grid for c in r if c]
            seq = [re.sub(r'</?strong>', '', x) for x in seq]
            out.append({'t': 'ul', 'items': [{'html': x, 'sub': []} for x in seq], 'cols': (min(3, ncols) if ncols > 1 else 2) if len(seq) >= 6 else 1, 'kind': 'label', 'from': 'table-list'})
            return
    # layout table: caption rows (a row of pictures followed by a row of short texts) are joined, the rest is read cell by cell
    r = 0
    while r < len(rows):
        cells = rows[r]
        only_imgs = all((td.find('img') is not None and not text_of(td)) or not (text_of(td) or td.find('img')) for td in cells) and any(td.find('img') for td in cells)
        nxt = rows[r + 1] if r + 1 < len(rows) else None
        if only_imgs and nxt and all(cell_is_simple(td) for td in nxt) and any(text_of(td) for td in nxt):
            figs = []
            for ci, td in enumerate(cells):
                for im in td.find_all('img'):
                    f = fig_from_img(im, ctx['page'])
                    if f:
                        if ci < len(nxt): f['cap'] = clean_inline(inline_html(nxt[ci], ctx)) or None
                        figs.append(f)
            if figs: out.append({'t': 'figs', 'figs': figs})
            r += 2
            continue
        row_figs = []
        for td in cells:
            sub = []
            walk(td, ctx, sub)
            # a cell that is "picture + one short line" is a captioned picture
            if len(sub) == 2 and sub[0]['t'] == 'figs' and len(sub[0]['figs']) == 1 and sub[1]['t'] in ('p', 'h') and words(plain(sub[1]['html'])) <= 12:
                sub[0]['figs'][0]['cap'] = sub[1]['html']
                row_figs.append(sub[0]['figs'][0]); continue
            if len(sub) == 1 and sub[0]['t'] == 'figs' and len(sub[0]['figs']) == 1:
                row_figs.append(sub[0]['figs'][0]); continue
            if row_figs:
                out.append({'t': 'figs', 'figs': row_figs}); row_figs = []
            out.extend(sub)
        if row_figs:
            out.append({'t': 'figs', 'figs': row_figs})
        r += 1


# ---------------------------------------------------------------- post-processing
def looks_like_label(t):
    """A short line without sentence punctuation, written Like A Title."""
    p = plain(t)
    if not p or '<a ' in t or '<br' in t or words(p) > 16 or re.search(r'[.!?;,:]$', p):
        return False
    ws_ = [w for w in re.findall(r"[A-Za-z][A-Za-z'’/&-]*", p)]
    big = [w for w in ws_ if len(w) > 3]
    if not big:
        return words(p) <= 3
    return sum(w[0].isupper() for w in big) / len(big) >= 0.6


def promote_labels(blocks):
    """Short title-like lines that introduce the pictures / list / paragraph below them become sub-headings."""
    out = []
    for i, b in enumerate(blocks):
        nxt = blocks[i + 1] if i + 1 < len(blocks) else None
        if b['t'] == 'p' and nxt is not None and nxt['t'] in ('figs', 'ul', 'ol', 'p') and looks_like_label(b['html']):
            out.append({'t': 'h', 'lvl': 4, 'html': re.sub(r'</?strong>', '', b['html']), 'src': 'label'})
        else:
            out.append(b)
    return out


def tidy(blocks, captions=None):
    """Merge split lists, classify lists (short labels vs sentences) and attach picture captions.
    captions='after'  : the short line under a single picture is its caption
    captions='before' : the short line above a single picture is its caption"""
    res = []
    for b in blocks:
        # the old editor often wrote one <ul> per bullet: put neighbours back together
        if b['t'] in ('ul', 'ol') and res and res[-1]['t'] == b['t'] and not res[-1].get('from') and not b.get('from'):
            res[-1]['items'].extend(b['items'])
            continue
        res.append(b)
    for b in res:
        if b['t'] in ('ul', 'ol'):
            classify_list(b)
    def short(b):
        return b['t'] in ('p', 'h') and words(plain(b['html'])) <= 16
    if captions == 'after':
        out, i = [], 0
        while i < len(res):
            b = res[i]
            if b['t'] == 'figs' and len(b['figs']) == 1 and i + 1 < len(res) and short(res[i + 1]) and not b['figs'][0]['cap']:
                b['figs'][0]['cap'] = res[i + 1]['html']
                out.append(b); i += 2; continue
            out.append(b); i += 1
        res = out
    elif captions == 'before':
        out, i = [], 0
        while i < len(res):
            b = res[i]
            if short(b) and i + 1 < len(res) and res[i + 1]['t'] == 'figs' and len(res[i + 1]['figs']) == 1 and not res[i + 1]['figs'][0]['cap']:
                res[i + 1]['figs'][0]['cap'] = b['html']
                out.append(res[i + 1]); i += 2; continue
            out.append(b); i += 1
        res = out
    # neighbouring single captioned pictures form one row
    out = []
    for b in res:
        if (b['t'] == 'figs' and out and out[-1]['t'] == 'figs' and all(f['cap'] for f in b['figs']) and all(f['cap'] for f in out[-1]['figs'])
                and b.get('row') is None and len(out[-1]['figs']) < 3 and max(f['w'] for f in b['figs'] + out[-1]['figs']) <= 460):
            out[-1]['figs'].extend(b['figs'])
        else:
            out.append(b)
    return out


def classify_list(b, inherit=None):
    """'label' = every item is a short label (shown in the template's own list style);
    'text'  = sentences (shown as body copy).  Nested lists follow their parent."""
    def all_texts(lst):
        for it in lst['items']:
            yield plain(it['html'])
            for s in it['sub']:
                yield from all_texts(s)
    texts = list(all_texts(b))
    longest = max([words(t) for t in texts] or [0])
    if inherit:
        b['kind'] = inherit
    elif b.get('kind') is None:
        b['kind'] = 'label' if longest <= 7 and not any(re.search(r'[.;]\s', t) or t.endswith('.') for t in texts) else 'text'
    for it in b['items']:
        for s in it['sub']:
            classify_list(s, b['kind'])
    return b


def outline(blocks, indent=''):
    lines = []
    for b in blocks:
        if b['t'] == 'h':
            lines.append(f"{indent}H{b['lvl']}  {plain(b['html'])}")
        elif b['t'] == 'p':
            t = plain(b['html'])
            lines.append(f"{indent}p    {t[:110]}{'…' if len(t) > 110 else ''}  [{words(t)}w]")
        elif b['t'] in ('ul', 'ol'):
            lines.append(f"{indent}{b['t']}   {len(b['items'])} items, cols={b['cols']}, kind={b['kind']}{' <' + b['from'] + '>' if b.get('from') else ''}")
            for it in b['items'][:60]:
                t = plain(it['html'])
                lines.append(f"{indent}     - {t[:96]}{'…' if len(t) > 96 else ''}")
                for s in it['sub']:
                    lines.extend(outline([s], indent + '         '))
        elif b['t'] == 'figs':
            lines.append(f"{indent}figs " + ' | '.join(f"{os.path.basename(f['src'])} {f['w']}x{f['h']}" + (f" «{plain(f['cap'])}»" if f['cap'] else '') for f in b['figs']))
    return lines


# ---------------------------------------------------------------- page level
def k2_item(rel, captions=None, labels=False):
    """A K2 item page (product / service detail or news item)."""
    s = soup(rel)
    ctx = {'page': rel, 'emails': cloak_emails(rel)}
    blocks = []
    for sel in ('div.itemIntroText', 'div.itemFullText'):
        el = s.select_one(sel)
        if el is not None:
            walk(el, ctx, blocks)
    blocks = tidy(blocks, captions)
    if labels:
        blocks = promote_labels(blocks)
    lead = s.select_one('div.itemImageBlock img')
    cat = s.select_one('.category-name a')
    return {'rel': rel, 'k2title': html.unescape(ws(lead.get('alt') or '')).strip() if lead is not None else None, 'blocks': blocks, 'lead': lead.get('src') if lead is not None else None,
            'category': text_of(cat) if cat is not None else None,
            'doc_title': text_of(s.title).replace(' - Advance Automation Sdn Bhd', ''),
            'meta_desc': (s.find('meta', attrs={'name': 'description'}) or {}).get('content')}


CAPTIONS = {'12-advance-automation-officially-launch': 'after', '23-mou-with-ramacon-corporation': 'after', '14-multiple-distributorships-awards': 'before',
            'calibration-certification-services': 'after'}

if __name__ == '__main__':
    import sys
    for rel in sys.argv[1:]:
        it = k2_item(rel, captions=CAPTIONS.get(rel.split('/')[-1]), labels='news-n-events' not in rel)
        print('=' * 20, rel, '|', it['doc_title'], '| k2:', it['k2title'], '| cat:', it['category'])
        print('\n'.join(outline(it['blocks'])))
    if MISSING_IMAGES:
        print('MISSING', MISSING_IMAGES)


# ---------------------------------------------------------------- the structured pages (home, about, lists ...)
def _t(el):
    return text_of(el) if el is not None else None


def _module(s, heading=None, cls=None):
    for m in s.select('div.t3-module'):
        if cls and cls in (m.get('class') or []):
            return m
        if heading and _t(m.select_one('h3.module-title')) and _t(m.select_one('h3.module-title')).lower() == heading.lower():
            return m
    return None


def home():
    s = BeautifulSoup(raw('index').replace('</br>', '<br />'), 'html5lib')
    d = {}
    # slideshow
    d['slides'] = []
    for li in s.select('.tp-banner li, .rev_slider li, .slideshow li, #slideshow li'):
        pass
    # captions live in the slider markup; read them by their classes
    caps = [ws(x.get_text(' ')).strip() for x in s.select('.tp-caption.big-title, .tp-caption .big-title, .slide-title, .tp-caption h2')]
    d['slides_raw'] = caps
    w = _module(s, cls='too-welcome')
    col = w.select('div.row > div')[0]
    d['welcome'] = {
        'title': _t(col.h2), 'sub': _t(col.h4),
        'paras': [text_of(p) for p in col.find_all('p', recursive=False) if text_of(p) and text_of(p) != 'Call us'],
        'button': (_t(col.select_one('a.btn')), col.select_one('a.btn')['href']),
        'call': (_t(col.select_one('.intro-contact p')), _t(col.select_one('.intro-contact a')), col.select_one('.intro-contact a')['href']),
        'iso_badge': col.select('img')[-1]['src'], 'iso_badge_alt': col.select('img')[-1].get('alt'),
    }
    d['credentials'] = [{'title': _t(b.h4), 'text': _t(b.p)} for b in w.select('.features-box')]
    d['certificates'] = [im['src'] for im in w.select('div.custom > p img')]
    sv = _module(s, cls='service-section')
    d['services_title'] = _t(sv.select_one('h3.module-title'))
    d['services'] = [{'img': it.select_one('img')['src'], 'title': _t(it.h4), 'text': _t(it.p), 'href': it.select_one('.item-content a')['href']} for it in sv.select('.service .item')]
    d['stats'] = [{'n': _t(c), 'label': _t(c.find_next('h4'))} for c in s.select('.too-counter')]
    wd = _module(s, cls='what-we-do')
    d['what_we_do'] = {'title': _t(wd.select_one('h3.module-title')), 'text': _t(wd.select_one('.our-features p')), 'tags': [_t(a) for a in wd.select('a.feature-block')]}
    dl = _module(s, cls='too-reports')
    d['downloads'] = [{'title': _t(a.h4), 'file': _t(a.span), 'href': a['href']} for a in dl.select('.too-brochure a')]
    wc = _module(s, heading='Why choose us')
    d['why'] = {'title': _t(wc.select_one('h3.module-title')), 'items': [{'title': _t(li.h4), 'text': _t(li.p)} for li in wc.select('.choose-us li')]}
    ln = _module(s, cls='latest-news')
    d['latest_title'] = _t(ln.select_one('h3.module-title'))
    d['latest'] = [a['href'].rstrip('/').split('/')[-1] for a in ln.select('a.moduleItemTitle')]
    return d


def slides():
    """Slide captions of the home page slideshow (text + the two buttons)."""
    h = raw('index')
    s = BeautifulSoup(h.replace('</br>', '<br />'), 'html5lib')
    out = []
    for li in s.select('li[data-transition], .tp-banner ul > li, .fullwidthbanner ul > li'):
        im = li.find('img')
        texts = [ws(c.get_text(' ')).strip() for c in li.select('.tp-caption') if ws(c.get_text(' ')).strip()]
        links = [(text_of(a), a.get('href')) for a in li.select('a')]
        out.append({'img': im.get('src') if im else None, 'texts': texts, 'links': links})
    return out


def about():
    s = soup('about-us')
    m = _module(s, cls='about-intro')
    cols = m.select('div.custom > div.row > div')
    left, right = cols[0], cols[1]
    d = {
        'images': [im['src'] for im in left.select('img')],
        'motto_title': _t(left.select_one('.motto-header h3')),
        'motto': [text_of(li) for li in left.select('.our-motto li')],
        'title': _t(right.h2), 'sub': _t(right.h4),
        'lead': _t(right.select('p.about-text')[0]),
        'roles': [text_of(li) for li in right.select('ul li')],
        'paras': [text_of(p) for p in right.select('p.about-text')[1:]],
        'boxes': [{'title': _t(b.h4), 'text': _t(b.p)} for b in right.select('.about-box')],
    }
    m2 = [x for x in s.select('div.t3-module') if x.select('.features-padding')][0]
    d['features'] = [{'title': _t(f.h4), 'text': _t(f.p)} for f in m2.select('.features-padding')]
    # "Industries leader" block with the counters
    c0 = s.select_one('.too-counter')
    blk = c0
    while blk is not None and blk.find('h3') is None and blk.find('h2') is None:
        blk = blk.parent
    d['leader'] = {'title': _t(blk.find(['h2', 'h3'])), 'text': ' '.join(text_of(p) for p in blk.find_all('p') if text_of(p))}
    d['stats'] = [{'n': _t(c), 'label': _t(c.find_next('h4'))} for c in s.select('.too-counter')]
    return d


def services():
    s = soup('products-and-services')
    return [{'img': it.select_one('img')['src'], 'title': _t(it.h4), 'text': _t(it.p), 'href': it.select_one('.item-content a')['href']} for it in s.select('.service-gray .item, .service .item')]


def category(slug):
    s = soup('products-and-services/' + slug)
    return {'title': _t(s.select_one('.itemListCategory h2')), 'doc_title': text_of(s.title).replace(' - Advance Automation Sdn Bhd', ''),
            'items': [{'title': _t(a), 'href': a['href']} for a in s.select('.catItemView h3.catItemTitle a, .catItemView .catItemTitle a')]}


def news_index():
    out = []
    for page in ('news-n-events', 'news-n-events__start-6'):
        s = soup(page)
        for it in s.select('.catItemView'):
            a = it.select_one('.catItemTitle a')
            intro = it.select_one('.catItemIntroText')
            im = it.select_one('.catItemImage img, .catItemImageBlock img')
            out.append({'slug': a['href'].rstrip('/').split('/')[-1], 'title': _t(a), 'intro': _t(intro), 'img': im['src'] if im is not None else None})
    return out


def news_dates():
    """Publication date of each news item (schema.org datePublished in the item page)."""
    out = {}
    for f in sorted(glob.glob(f'{SRC}/pages/news-n-events/item/*.html')):
        h = open(f, encoding='utf-8').read()
        m = re.search(r'"datePublished"\s*:\s*"([0-9T:+-]+)"', h) or re.search(r'(20[01]\d-\d\d-\d\dT[0-9:+]+)', h)
        out[os.path.basename(f)[:-5]] = m.group(1)[:10] if m else None
    return out


def clients():
    s = soup('clients')
    return {'title': _t(s.select_one('h2.itemTitle')), 'logos': [{'src': im['src'], 'alt': ws(im.get('alt') or '').strip()} for im in s.select('.clients-logo img')]}


def contact():
    s = soup('contact')
    m = [x for x in s.select('div.t3-module') if 'contact-us' in (x.get('class') or [])][0]
    cols = m.select('.myicon-col')
    form = s.find('form', id='userForm')
    return {'title': _t(m.select_one('h2.module-title')), 'lead': _t(m.h4),
            'blocks': [{'label': _t(c.h5), 'html': clean_inline(inline_html(c.select_one('.col-content'), {'emails': cloak_emails('contact'), 'page': 'contact'}))} for c in cols],
            'form_title': None,
            'fields': [{'label': text_of(l).replace('**', '').strip().rstrip(':'), 'required': '**' in text_of(l), 'for': l.get('for')} for l in form.find_all('label') if text_of(l)],
            'submit': _t(form.find('button', attrs={'type': 'submit'}))}
