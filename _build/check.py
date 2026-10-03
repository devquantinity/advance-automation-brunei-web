"""Static checks over the generated pages: links, assets, leftovers of template sample content, headings, meta.

    python3 _build/check.py

Run after build.py; it reads the list of pages that build.py wrote (_build/pages.json)."""
import json, os, re, sys
from bs4 import BeautifulSoup
from urllib.parse import unquote, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE)
P = json.load(open(f'{HERE}/pages.json'))
urls = {p['url'] for p in P}

# external links that are part of the live site's own content (footer credit, links inside articles)
EXTERNAL_OK = {'gotka.com', 'www.gj.com', 'www.easa.com', 'www.nema.org', 'www.iec.ch'}
# hosts the template itself loads from (web font)
ASSET_HOSTS = ('fonts.googleapis.com', 'fonts.gstatic.com', 'ajax.googleapis.com')
# sample content of the template that must not survive on a page
LEFTOVER = ['This is some text inside of a div block', 'Lorem', 'example.com', '(888)', 'Riverbend', 'Veltom', 'Webflow', 'webflow.io', '{Name}', 'Sophia Lee',
            'Start Your Project', 'Get started', 'Inquire Now', 'View Services', 'Author-', 'Small-author', '/_template/',
            'facebook.com', 'instagram.com', 'dribbble.com', 'behance.net', 'whatsapp.com', 'twitter.com', 'linkedin.com', 'youtube.com']
WS = re.compile(r'\s+')
problems = 0


def bad(page, msg):
    global problems
    problems += 1
    print(f'  [{page}] {msg}')


def exists(page_file, ref):
    ref = ref.split('#')[0].split('?')[0]
    if not ref:
        return True
    if ref.startswith('/'):
        path = os.path.join(OUT, unquote(ref).lstrip('/'))
    else:
        path = os.path.normpath(os.path.join(os.path.dirname(os.path.join(OUT, page_file)), unquote(ref)))
    return os.path.isfile(path)


for p in P:
    f = p['file']
    html = open(os.path.join(OUT, f), encoding='utf-8').read()
    s = BeautifulSoup(html, 'html5lib')

    # --- links
    for a in s.find_all('a'):
        h = a.get('href')
        if h is None:
            bad(f, f'a without href: {str(a)[:80]}')
        elif h.startswith(('mailto:', 'tel:')):
            pass
        elif h.startswith('http'):
            if urlparse(h).netloc not in EXTERNAL_OK:
                bad(f, f'external link {h}')
        elif h == '#':
            # the drawn submit button of the contact form is the only place where the template uses "#"
            if not ('fda-button-main' in (a.get('class') or []) and a.find_parent('form') is not None):
                bad(f, f'href="#" on {" ".join(a.get("class") or [])[:60]} :: {a.get_text(" ", strip=True)[:40]}')
        elif re.search(r'\.(png|jpe?g|webp|gif|pdf|svg)$', h, re.I):
            if not exists(f, h):
                bad(f, f'missing file linked: {h}')
        elif (h.split('#')[0].rstrip('/') or '/') not in urls:
            bad(f, f'internal link to unknown page: {h}')

    # --- assets
    refs = []
    for tag, attr in (('img', 'src'), ('script', 'src'), ('link', 'href'), ('source', 'src'), ('video', 'poster')):
        refs += [el.get(attr) for el in s.find_all(tag) if el.get(attr)]
    for el in s.find_all(['img', 'source']):
        refs += [part.strip().split(' ')[0] for part in (el.get('srcset') or '').split(',') if part.strip()]
    refs += [el['data-poster-url'] for el in s.find_all(attrs={'data-poster-url': True})]
    for el in s.find_all(attrs={'data-video-urls': True}):
        refs += el['data-video-urls'].split(',')
    refs += [m.group(1) for m in re.finditer(r'url\((?:&quot;|["\'])?([^)"\'&]+)', html)]
    for r in refs:
        if r.startswith(('http://', 'https://', 'data:')):
            if not (r.startswith('data:') or any(x in r for x in ASSET_HOSTS) or r.startswith('https://advanceautomationbrunei.com/')):
                bad(f, f'external asset {r[:90]}')
        elif not exists(f, r):
            bad(f, f'missing asset {r[:100]}')

    # --- leftovers of the template's sample content
    for w in LEFTOVER:
        if w in html:
            i = html.index(w)
            bad(f, f'leftover "{w}": …{WS.sub(" ", html[max(0, i - 60):i + 60])}…')

    # --- structure
    if f != '404.html':
        if len(s.find_all('h1')) != 1:
            bad(f, f'{len(s.find_all("h1"))} h1 elements')
        d = s.find('meta', attrs={'name': 'description'})
        if not d or len(d.get('content', '')) < 50:
            bad(f, f'weak description: {d.get("content") if d else None}')
    if not s.title or not s.title.string.strip():
        bad(f, 'no title')
    for img in s.find_all('img'):
        if img.get('alt') is None:
            bad(f, f'img without alt: {img.get("src")[-50:]}')
    ids = [e.get('id') for e in s.find_all(id=True)]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        bad(f, f'duplicate ids: {sorted(dup)[:5]}')

print(f'{len(P)} pages checked, {problems} problems')
sys.exit(1 if problems else 0)
