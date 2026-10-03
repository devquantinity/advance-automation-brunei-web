"""Core of the Advance Automation site generator.

Every page is assembled from sections that already exist in the Veltom template (taken from the template's own
HTML files in _template/ with BeautifulSoup) and filled with text / pictures of the live advanceautomationbrunei.com
site (scraped into source-site/).
No section markup is invented here; helper functions only change text, links, pictures and repeat or remove
existing children.
"""
import copy, os, re, html, json, subprocess, shutil
from bs4 import BeautifulSoup, NavigableString, Tag

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get('AAB_ROOT') or os.path.dirname(HERE)      # the project folder
TPL = f'{ROOT}/_template'               # the Veltom demo pages: where every section comes from
SRC = f'{ROOT}/source-site'             # the scrape of the live site: where every text and picture comes from
OUT = os.environ.get('AAB_OUT') or ROOT # where the pages are written (the project folder itself)
DOMAIN = 'https://advanceautomationbrunei.com'
SITE_NAME = 'Advance Automation Sdn Bhd'
ASSET = '@@/'                           # placeholder for "path back to the site root"

_cache = {}


def tpl(page):
    """Parsed template page (cached). page is relative to _template/, e.g. 'contact.html' or 'blog-post/x.html'."""
    if page not in _cache:
        h = open(f'{TPL}/{page}', encoding='utf-8').read()
        _cache[page] = BeautifulSoup(h, 'html5lib')
    return _cache[page]


ASSET_RE = re.compile(r'(?<![\w/.@-])(?:\.\./)*(images|videos|documents|css|js)/')


def norm_assets(s):
    """images/x.png, ../images/x.png ... -> @@/images/x.png"""
    return ASSET_RE.sub(lambda m: ASSET + m.group(1) + '/', s)


def sec(page, selector, index=0):
    """A fresh copy of one element of a template page, with asset paths normalised."""
    el = tpl(page).select(selector)[index]
    c = BeautifulSoup(norm_assets(str(el)), 'html5lib').body.contents[0]
    return c.extract()


def frag(markup):
    """Parse a small piece of markup into a list of nodes."""
    b = BeautifulSoup('<div id="__f">' + markup + '</div>', 'html5lib').find(id='__f')
    return [n.extract() for n in list(b.contents)]


def set_text(el, text):
    el.clear()
    el.append(NavigableString(text))
    return el


def set_html(el, markup):
    el.clear()
    for n in frag(markup):
        el.append(n)
    return el


def clone(el):
    return copy.copy(el)


def esc(s):
    return html.escape(s, quote=False)


# ------------------------------------------------------------------ small template idioms
def set_button(a, label, href):
    """The template's animated button holds its label twice (rest / hover state)."""
    for t in a.select('.fda-button-text-1, .fda-button-text-2'):
        set_text(t, label)
    a['href'] = href
    for k in ('aria-current',):
        if a.has_attr(k): del a[k]
    if 'w--current' in a.get('class', []):
        a['class'] = [c for c in a['class'] if c != 'w--current']
    return a


def set_label(root, text):
    """Small dotted label above a heading (.fda-sub-wrap).  text=None removes it."""
    w = root.select_one('.fda-sub-wrap')
    if w is None:
        return
    if text is None:
        w.decompose()
    else:
        set_text(w.select_one('.fda-sub-text'), text)


def img_set(img, src, alt='', width=None, height=None, keep_srcset=False):
    img['src'] = src if src.startswith(ASSET) or src.startswith('http') else ASSET + src
    img['alt'] = alt
    if not keep_srcset:
        for k in ('srcset', 'sizes'):
            if img.has_attr(k): del img[k]
    if width: img['width'] = str(width)
    elif img.has_attr('width'): del img['width']
    if height: img['height'] = str(height)
    elif img.has_attr('height'): del img['height']
    return img


_tpl_imgs = None


def tpl_img_attrs(filename_part):
    """One of the template's own pictures with its responsive variants (the -p-500 ... files Webflow generated),
    so a re-used template picture stays as sharp and as light as in the template."""
    global _tpl_imgs
    from PIL import Image
    if _tpl_imgs is None:
        _tpl_imgs = {}
        d = f'{ROOT}/images'
        files = [f for f in os.listdir(d) if os.path.isfile(f'{d}/{f}')]
        variants = {}
        for f in files:
            m = re.match(r'^(.*)-p-(\d+)(\.[A-Za-z0-9]+)$', f)
            if m:
                variants.setdefault((m.group(1) + m.group(3)).lower(), []).append((int(m.group(2)), f))
        for f in files:
            if re.search(r'-p-\d+\.', f):
                continue
            _tpl_imgs[f] = sorted(variants.get(f.lower(), []))
    hits = [k for k in _tpl_imgs if filename_part in k]
    if not hits:
        raise KeyError(filename_part)
    f = sorted(hits, key=len)[0]
    srcset = None
    if _tpl_imgs[f]:
        with Image.open(f'{ROOT}/images/{f}') as im:
            w = im.size[0]
        from urllib.parse import quote
        srcset = ', '.join([f'{ASSET}images/{quote(v)} {n}w' for n, v in _tpl_imgs[f]] + [f'{ASSET}images/{quote(f)} {w}w'])
    from urllib.parse import quote as q
    return {'src': f'{ASSET}images/{q(f)}', 'srcset': srcset}


def use_tpl_img(img, filename_part, alt='', sizes='100vw'):
    a = tpl_img_attrs(filename_part)
    img['src'] = a['src']
    img['alt'] = alt
    if a['srcset']:
        img['srcset'] = a['srcset']; img['sizes'] = sizes
    else:
        for k in ('srcset', 'sizes'):
            if img.has_attr(k): del img[k]
    for k in ('width', 'height'):
        if img.has_attr(k): del img[k]
    return img


# ------------------------------------------------------------------ page writer
HEAD = '''<!doctype html>
<html data-wf-domain="advanceautomationbrunei.com" data-wf-page="{wf_page}" data-wf-site="69b2a15200bc2cb1d23ead7e" lang="en">
<head>
<meta charset="utf-8" />
<title>{title}</title>
<meta content="{desc}" name="description" />
<meta content="{title}" property="og:title" />
<meta content="{desc}" property="og:description" />
<meta content="{og_image}" property="og:image" />
<meta content="{title}" name="twitter:title" />
<meta content="{desc}" name="twitter:description" />
<meta content="{og_image}" name="twitter:image" />
<meta content="{og_type}" property="og:type" />
<meta content="{canonical}" property="og:url" />
<meta content="summary_large_image" name="twitter:card" />
<meta content="width=device-width, initial-scale=1" name="viewport" />
<link href="{canonical}" rel="canonical" />
<link href="@@/css/veltom.shared.7640c260e.css" rel="stylesheet" type="text/css" />
<link href="@@/css/aab.css" rel="stylesheet" type="text/css" />
<link href="https://fonts.googleapis.com" rel="preconnect" />
<link crossorigin="anonymous" href="https://fonts.gstatic.com" rel="preconnect" />
<script src="https://ajax.googleapis.com/ajax/libs/webfont/1.6.26/webfont.js" type="text/javascript"></script>
<script type="text/javascript">
WebFont.load({{ google: {{ families: ["Source Sans 3:300,400,500,600,700"] }} }});
</script>
<script type="text/javascript">
!(function (o, c) {{
var n = c.documentElement, t = " w-mod-";
(n.className += t + "js"), ("ontouchstart" in o || (o.DocumentTouch && c instanceof DocumentTouch)) && (n.className += t + "touch");
}})(window, document);
</script>
<link href="@@/images/aab/favicon.ico" rel="shortcut icon" type="image/x-icon" />
<link href="@@/images/aab/webclip.png" rel="apple-touch-icon" />
</head>
'''

CHUNKS = {'base': 'site.19f039a5.7eb409ed3c628be4.js', 'forms': 'site.5cf30428.626258d0ccb0826f.js', 'tabs': 'site.bc1050cb.20fb869f3418002f.js'}
FOOT = '''<script src="@@/js/jquery-3.5.1.min.dc5e7f18c8.js" type="text/javascript"></script>
<script src="@@/js/site.schunk.36b8fb49256177c8.js" type="text/javascript"></script>
<script src="@@/js/site.schunk.ef3d838b12b5ed87.js" type="text/javascript"></script>
<script src="@@/js/{chunk}" type="text/javascript"></script>
</body>
</html>
'''

PAGES = []          # registry of everything written (url, file, title) for the link checker and the report


def clean_desc(s, limit=158):
    s = html.unescape(html.unescape(s or ''))
    s = re.sub(r'\s+', ' ', s.replace('\xa0', ' ')).strip()
    if len(s) > limit:
        s = s[:limit].rsplit(' ', 1)[0].rstrip(' ,;:-') + '…'
    return s


def write_page(url, title, desc, body_nodes, wf_page, chunk='base', og_image=None, og_type='website', main_class=None, main=True, nav=None, footer=None, raw_doc_title=None,
               body_class=None, before_nav=None):
    """url = path as on the live site ('/' or '/about-us').  Pages are written as <url>/index.html so that the
    clean URLs work on any static host without rewrite rules.
    main_class / body_class / before_nav: what the template page has around its sections (only the home page has any)."""
    rel = 'index.html' if url == '/' else url.strip('/') + '/index.html'
    depth = 0 if url == '/' else len(url.strip('/').split('/'))
    full_title = raw_doc_title or (f'{title} - {SITE_NAME}')
    head = HEAD.format(wf_page=wf_page, title=html.escape(full_title, quote=True), desc=html.escape(clean_desc(desc), quote=True),
                       og_image=og_image or f'{DOMAIN}/images/aab/og-image.jpg', og_type=og_type, canonical=DOMAIN + (url if url != '/' else '/'))
    parts = [head, f'<body class="{body_class}">\n' if body_class else '<body>\n']
    for n in (before_nav or []): parts.append(str(n))
    if nav is not None: parts.append(str(nav))
    if main:
        parts.append(f'<main class="{main_class}">' if main_class else '<main>')
    for n in body_nodes:
        parts.append(n if isinstance(n, str) else str(n))
    if main:
        parts.append('</main>')
    if footer is not None: parts.append(str(footer))
    parts.append(FOOT.format(chunk=CHUNKS[chunk]))
    doc = '\n'.join(parts)
    doc = re.sub(r'\s+aria-label="[^"]*\{Name\}[^"]*"', '', doc)       # unfilled CMS placeholder labels of the template
    doc = norm_assets(doc)
    doc = doc.replace(ASSET, '../' * depth)
    path = f'{OUT}/{rel}'
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(doc)
    PAGES.append({'url': url, 'file': rel, 'title': full_title})
    return path


def prettier(paths):
    """Same settings as webformatter.com/html (Prettier 3.3.3, 120 columns, 4 spaces)."""
    script = f'{HERE}/format.mjs'
    for i in range(0, len(paths), 40):
        r = subprocess.run(['node', script] + paths[i:i + 40], capture_output=True, text=True, cwd=HERE)
        if r.returncode != 0:
            raise RuntimeError('Formatting failed (is Prettier installed?  run "npm install" in _build/).\n' + r.stdout[-2000:] + r.stderr[-3000:])
