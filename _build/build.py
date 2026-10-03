"""Build the Advance Automation pages into the project folder.

    python3 _build/build.py            every page
    python3 _build/build.py home about only the named groups
                                       (details news home about products categories clients newslist contact notfound)

Sections come from _template/, text and pictures from source-site/; nothing else is written into the pages.
The pages are formatted with Prettier exactly like webformatter.com/html does (see format.mjs).
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *
import richtext as RT

JS_MAIN = 'js/site.schunk.ef3d838b12b5ed87.js'
JS_NOTE = ('/* AAB: (1) the home-two hero lives on the home page, so its 10 scroll-into-view triggers were re-pointed to the home page id (...ad67). '
           '(2) Element interactions are no longer tied to the template page they were designed on (the page-id check in the interaction engine\'s element lookup is switched off), '
           'so a template section keeps its animations on whichever page uses it. Page-level events are unchanged. '
           '(3) The logo strip on the home page carries 11 client logos instead of 5 sample logos; it scrolls one group width per loop, so its trigger (e-1582) '
           'uses a copy of the "Marquee v2" action list (a-203-aab) whose loop time is longer in the same proportion - the strip moves at the template\'s pace. */')
MARQUEE_TEMPLATE_GROUP = 5 * (140 + 160)          # five 140px logos with 5rem side paddings, moved in 30 s


def patch_js(marquee_width):
    """The three changes to the template's interaction script described in JS_NOTE.  Safe to run again."""
    p = f'{OUT}/{JS_MAIN}'
    s = open(p, encoding='utf-8').read()
    before = s
    # (2) element lookups are not page-scoped
    orig, new = 'if(a=t[1],d!==document.documentElement.getAttribute(r))return null', 'if(a=t[1],!1)return null'
    if orig in s:
        assert s.count(orig) == 1
        s = s.replace(orig, new)
    assert s.count(new) == 1
    # (3) home logo strip: the template's pace with more logos
    ms = round(30 * marquee_width / MARQUEE_TEMPLATE_GROUP) * 1000
    if '"a-203-aab":{' not in s:
        i = s.index('"a-203":{'); j = s.index('},"a-', i) + 1
        al = s[i:j]
        assert al.count('duration:3e4') == 1
        s = s[:j] + ',' + al.replace('a-203', 'a-203-aab').replace('duration:3e4', f'duration:{ms}') + s[j:]
    else:
        i = s.index('"a-203-aab":{'); j = s.index('},"a-', i) + 1
        al, n = re.subn(r'(id:"a-203-aab-n-2",.*?duration:)\d+', lambda m: m.group(1) + str(ms), s[i:j], count=1)
        assert n == 1
        s = s[:i] + al + s[j:]
    k = s.index('"e-1582":{'); seg = s[k:k + 400]
    if 'actionListId:"a-203-aab"' not in seg:
        assert seg.count('actionListId:"a-203"') == 1
        s = s[:k] + seg.replace('actionListId:"a-203"', 'actionListId:"a-203-aab"') + s[k + 400:]
    s, n = re.subn(r'^/\* AAB:.*?\*/', lambda m: JS_NOTE, s, count=1, flags=re.S)
    assert n == 1 and s.startswith(JS_NOTE)
    if s != before:
        open(p, 'w', encoding='utf-8').write(s)
    return s != before


def main():
    import pages
    RT.COPIED.clear(); PAGES.clear()
    todo = sys.argv[1:] or ['all']
    patched = patch_js(pages.marquee_group_width(pages.A.clients()['logos']))
    def want(k): return 'all' in todo or k in todo
    if want('details'): pages.build_details()
    if want('news'): pages.build_news_items()
    for name in ('home', 'about', 'products', 'categories', 'clients', 'newslist', 'contact', 'notfound'):
        if want(name): getattr(pages, 'build_' + name)()
    pages.share_image()
    n = RT.copy_images()
    prettier([f'{OUT}/{p["file"]}' for p in PAGES])
    if 'all' in todo:
        json.dump(PAGES, open(f'{HERE}/pages.json', 'w'), indent=1)
    print(f'{len(PAGES)} pages written, {n} pictures copied to images/aab/' + (', interaction script patched' if patched else ''))
    missing = sorted(set(pages.A.MISSING_IMAGES))
    if missing:
        print(f'{len(missing)} pictures referenced by the live pages do not exist on the live site (left out):')
        for page, src in missing: print(f'   {page}: {src}')


if __name__ == '__main__':
    main()
