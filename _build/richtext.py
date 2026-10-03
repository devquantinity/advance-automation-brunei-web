"""Render the block model of aabcontent.py as Webflow rich text (the element the template uses for its articles)."""
import html, os, shutil
from core import ASSET, OUT

COPIED = {}      # site path -> source file, for pictures that have to be copied into images/aab/


def _img(f, eager=False):
    COPIED[f['src']] = f['file']
    alt = html.escape(f['alt'] or '', quote=True)
    return f'<img alt="{alt}" height="{f["h"]}" loading="{"eager" if eager else "lazy"}" src="{ASSET}{f["src"]}" width="{f["w"]}" />'


def figure(f, align='center'):
    cap = f'<figcaption>{f["cap"]}</figcaption>' if f.get('cap') else ''
    return (f'<figure class="w-richtext-align-{align} w-richtext-figure-type-image" style="width: {f["w"]}px; max-width: 100%">'
            f'<div>{_img(f)}</div>{cap}</figure>')


def _list(b):
    tag = b['t']
    cls = []
    if b.get('kind') == 'text': cls.append('aab-list-text')
    if b.get('cols', 1) > 1: cls.append(f'aab-cols-{b["cols"]}')
    out = [f'<{tag}' + (f' class="{" ".join(cls)}"' if cls else '') + '>']
    for it in b['items']:
        sub = ''.join(_list(s) for s in it['sub'])
        out.append(f'<li>{it["html"]}{sub}</li>')
    out.append(f'</{tag}>')
    return ''.join(out)


def render(blocks):
    out = []
    for b in blocks:
        t = b['t']
        if t == 'h':
            out.append(f'<h{b["lvl"]}>{b["html"]}</h{b["lvl"]}>')
        elif t == 'p':
            out.append(f'<p>{b["html"]}</p>')
        elif t in ('ul', 'ol'):
            out.append(_list(b))
        elif t == 'figs':
            if len(b['figs']) == 1:
                out.append(figure(b['figs'][0]))
            else:
                out.append('<div class="aab-figure-row">' + ''.join(figure(f, 'normal') for f in b['figs']) + '</div>')
    return '\n'.join(out)


def copy_images():
    n = 0
    for site_path, src in COPIED.items():
        dst = os.path.join(OUT, site_path)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.isfile(dst) or os.path.getsize(dst) != os.path.getsize(src):
            shutil.copyfile(src, dst); n += 1
    return n
